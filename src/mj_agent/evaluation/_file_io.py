"""Private, bounded local IO. Handles anchor lookup; unsupported guards fail closed."""

from __future__ import annotations

import ctypes
import fnmatch
import os
import re
import sys
from pathlib import Path
from typing import Any

_MAX_BYTES = 10 * 1024 * 1024
_SECRET_DIRS = {".ssh", ".aws", ".azure", ".kube", ".gnupg"}
_SECRET_NAMES = {".netrc", "_netrc", "credentials", "credentials.json", "credentials.yml",
                 "credentials.yaml", "token", "token.json", "tokens.json", "id_rsa", "id_dsa",
                 "id_ecdsa", "id_ed25519"}


class _FileError(ValueError):
    """Contains only a fixed reason code, never an OS error or supplied path."""


def _lexical(raw: str) -> Path:
    value = raw.replace("\\", "/")
    if not value or "\x00" in value or value.startswith("//") or len(value) > 4096:
        raise _FileError("INPUT_PATH_REJECTED")
    drive = bool(re.match(r"^[A-Za-z]:/", value))
    if ":" in (value[2:] if drive else value):
        raise _FileError("INPUT_PATH_REJECTED")
    if os.name == "nt" and value.startswith("/"):
        raise _FileError("INPUT_PATH_REJECTED")
    for part in value.split("/"):
        if part == "..":
            raise _FileError("PATH_TRAVERSAL_FORBIDDEN")
        if part in {"", "."} or (drive and part == value[:2]):
            continue
        lower = part.casefold()
        if (lower.startswith(".env") or lower in _SECRET_DIRS or lower in _SECRET_NAMES
                or fnmatch.fnmatchcase(lower, "secrets*.enc")
                or lower.endswith((".pem", ".key", ".p12", ".pfx"))):
            raise _FileError("SECRET_PATH_FORBIDDEN")
        if os.name == "nt" and (
            part.endswith((".", " ")) or re.search(r"~[0-9]", part)
            or re.match(r"^(con|prn|aux|nul|clock\$|conin\$|conout\$|com[0-9¹²³]|lpt[0-9¹²³])(?:\.|$)", lower)
            or any(char in part for char in '<>"|?*')
        ):
            raise _FileError("AMBIGUOUS_WINDOWS_PATH_COMPONENT")
    if os.name != "nt" and value.startswith(("/proc/", "/sys/", "/dev/")):
        raise _FileError("INPUT_PATH_REJECTED")
    return Path(raw)


def _root(raw: Path | None) -> Path:
    path = _lexical(str(raw if raw is not None else Path.cwd()))
    if not path.is_absolute():
        raise _FileError("ABSOLUTE_ROOT_REQUIRED")
    return path


def _relative(root: Path, raw: str) -> tuple[str, ...]:
    path = _lexical(raw)
    absolute = path if path.is_absolute() else root / path
    if tuple(os.path.normcase(p) for p in absolute.parts[:len(root.parts)]) != tuple(
        os.path.normcase(p) for p in root.parts
    ):
        raise _FileError("PATH_OUTSIDE_ROOT")
    result = absolute.parts[len(root.parts):]
    if not result:
        raise _FileError("DESCENDANT_PATH_REQUIRED")
    return result


class _UnicodeString(ctypes.Structure):
    _fields_ = [("length", ctypes.c_uint16), ("maximum", ctypes.c_uint16), ("buffer", ctypes.c_void_p)]


class _ObjectAttributes(ctypes.Structure):
    _fields_ = [("length", ctypes.c_uint32), ("root", ctypes.c_void_p),
                ("name", ctypes.POINTER(_UnicodeString)), ("attributes", ctypes.c_uint32),
                ("security", ctypes.c_void_p), ("quality", ctypes.c_void_p)]


class _IoStatus(ctypes.Structure):
    _fields_ = [("status", ctypes.c_void_p), ("information", ctypes.c_size_t)]


class _FileInfo(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in (
        "attributes", "created_low", "created_high", "accessed_low", "accessed_high",
        "written_low", "written_high", "volume", "size_high", "size_low", "links",
        "index_high", "index_low",
    )]


class _WindowsIO:
    kernel: Any
    native: Any
    volume: int
    final_root: str

    def __init__(self, root: Path) -> None:
        self.root = root
        self.handles: dict[tuple[str, ...], int] = {}
        self.ancestors: list[int] = []
        if sys.platform != "win32":
            raise _FileError("FS_CAPABILITY_UNAVAILABLE")
        self.kernel: Any = ctypes.WinDLL("kernel32", use_last_error=True)
        self.native: Any = ctypes.WinDLL("ntdll", use_last_error=True)
        self._prototypes()
        if self.kernel.GetDriveTypeW(root.anchor) != 3:
            raise _FileError("FS_CAPABILITY_UNAVAILABLE")
        filesystem = ctypes.create_unicode_buffer(32)
        if (not self.kernel.GetVolumeInformationW(root.anchor, None, 0, None, None, None,
                                                  filesystem, len(filesystem))
                or filesystem.value != "NTFS"):
            raise _FileError("FS_CAPABILITY_UNAVAILABLE")
        try:
            handle = self.kernel.CreateFileW(root.anchor, 0x80000000, 1, None, 3,
                                             0x02300000, None)
            if handle in {None, ctypes.c_void_p(-1).value}:
                raise _FileError("FS_CAPABILITY_UNAVAILABLE")
            current = int(handle)
            self.ancestors.append(current)
            self.volume = self._info(current).volume
            for name in root.parts[1:]:
                current = self._open(current, name, directory=True)
                self.ancestors.append(current)
            self.handles[()] = current
            self.final_root = self._final(current)
        except Exception:
            self.close()
            raise

    def _prototypes(self) -> None:
        kernel = self.kernel
        kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                                      ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        kernel.CreateFileW.restype = ctypes.c_void_p
        kernel.GetDriveTypeW.argtypes = [ctypes.c_wchar_p]
        kernel.GetDriveTypeW.restype = ctypes.c_uint32
        kernel.GetVolumeInformationW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32,
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32]
        kernel.GetVolumeInformationW.restype = ctypes.c_int
        kernel.GetFileInformationByHandle.argtypes = [ctypes.c_void_p, ctypes.POINTER(_FileInfo)]
        kernel.GetFileInformationByHandle.restype = ctypes.c_int
        kernel.GetFileType.argtypes = [ctypes.c_void_p]
        kernel.GetFileType.restype = ctypes.c_uint32
        kernel.GetFinalPathNameByHandleW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p,
                                                   ctypes.c_uint32, ctypes.c_uint32]
        kernel.GetFinalPathNameByHandleW.restype = ctypes.c_uint32
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel.CloseHandle.restype = ctypes.c_int
        self.native.NtCreateFile.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint32,
            ctypes.POINTER(_ObjectAttributes), ctypes.POINTER(_IoStatus), ctypes.c_void_p,
            ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
            ctypes.c_void_p, ctypes.c_uint32]
        self.native.NtCreateFile.restype = ctypes.c_int32

    def _info(self, handle: int) -> _FileInfo:
        result = _FileInfo()
        if not self.kernel.GetFileInformationByHandle(handle, ctypes.byref(result)):
            raise _FileError("FS_CAPABILITY_UNAVAILABLE")
        if result.attributes & (0x400 | 0x1000 | 0x400000) or self.kernel.GetFileType(handle) != 1:
            raise _FileError("SPECIAL_FILE_PATH_FORBIDDEN")
        return result

    def _final(self, handle: int) -> str:
        buffer = ctypes.create_unicode_buffer(4096)
        size = self.kernel.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
        if not size or size >= len(buffer) or not buffer.value.startswith("\\\\?\\"):
            raise _FileError("FS_CAPABILITY_UNAVAILABLE")
        result = buffer.value[4:]
        _lexical(result)
        return os.path.normcase(result).rstrip("\\")

    def _open(self, parent: int, name: str, *, directory: bool,
              create: bool = False, writing: bool = False) -> int:
        buffer = ctypes.create_unicode_buffer(name)
        length = len(name.encode("utf-16-le"))
        if length > 65532:
            raise _FileError("INPUT_PATH_REJECTED")
        unicode = _UnicodeString(length, length + 2, ctypes.cast(buffer, ctypes.c_void_p))
        attributes = _ObjectAttributes(ctypes.sizeof(_ObjectAttributes), parent,
                                      ctypes.pointer(unicode), 0x40, None, None)
        status_block = _IoStatus()
        handle = ctypes.c_void_p()
        # The output handle also needs read-attributes for the same identity guards.
        access = (0x20 if directory else 0x40000000 if writing else 0x80000000) | 0x100000 | 0x80
        options = 0x00200000 | 0x20 | (1 if directory else 0x40 | 0x00400000)
        status = self.native.NtCreateFile(ctypes.byref(handle), access, ctypes.byref(attributes),
            ctypes.byref(status_block), None, 0x80, 1, 2 if create else 1, options, None, 0)
        if status < 0 or handle.value is None:
            reason = "OUTPUT_EXISTS" if create and (status & 0xffffffff) == 0xc0000035 else "LOCAL_IO_REJECTED"
            raise _FileError(reason)
        opened = int(handle.value)
        try:
            info = self._info(opened)
            if (bool(info.attributes & 0x10) != directory or info.volume != self.volume
                    or (not directory and info.links != 1)):
                raise _FileError("REGULAR_SINGLE_LINK_INPUT_REQUIRED")
            final = self._final(opened)
            if hasattr(self, "final_root") and not final.startswith(self.final_root + "\\"):
                raise _FileError("PATH_OUTSIDE_ROOT")
            return opened
        except Exception:
            self.kernel.CloseHandle(opened)
            raise

    def _directory(self, parts: tuple[str, ...]) -> int:
        current = self.handles[()]
        for index, name in enumerate(parts):
            key = parts[:index + 1]
            if key not in self.handles:
                self.handles[key] = self._open(current, name, directory=True)
            current = self.handles[key]
        return current

    @staticmethod
    def _identity(info: _FileInfo) -> tuple[int, ...]:
        return (info.volume, info.index_high, info.index_low, info.size_high, info.size_low,
                info.written_high, info.written_low, info.links, info.attributes)

    def read(self, parts: tuple[str, ...]) -> bytes:
        if sys.platform != "win32":
            raise _FileError("FS_CAPABILITY_UNAVAILABLE")
        import msvcrt
        handle = self._open(self._directory(parts[:-1]), parts[-1], directory=False)
        transferred = False
        try:
            before = self._info(handle)
            if ((before.size_high << 32) | before.size_low) > _MAX_BYTES:
                raise _FileError("INPUT_SIZE_LIMIT")
            descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
            transferred = True
            try:
                stream = os.fdopen(descriptor, "rb")
            except BaseException:
                os.close(descriptor)
                raise
            with stream:
                raw = stream.read(_MAX_BYTES + 1)
                if self._identity(before) != self._identity(self._info(handle)):
                    raise _FileError("FILE_CHANGED")
            if len(raw) > _MAX_BYTES:
                raise _FileError("INPUT_SIZE_LIMIT")
            return raw
        finally:
            if not transferred:
                self.kernel.CloseHandle(handle)

    def write(self, parts: tuple[str, ...], files: tuple[tuple[str, bytes], ...]) -> None:
        if sys.platform != "win32":
            raise _FileError("FS_CAPABILITY_UNAVAILABLE")
        import msvcrt
        output = self._open(self._directory(parts[:-1]), parts[-1], directory=True, create=True)
        self.handles[parts] = output
        for name, raw in files:
            handle = self._open(output, name, directory=False, create=True, writing=True)
            try:
                descriptor = msvcrt.open_osfhandle(handle, os.O_WRONLY | os.O_BINARY)
            except Exception:
                self.kernel.CloseHandle(handle)
                raise
            try:
                stream = os.fdopen(descriptor, "wb")
            except BaseException:
                os.close(descriptor)
                raise
            with stream:
                stream.write(raw)

    def close(self) -> None:
        failed = False
        for handle in reversed(self.ancestors + list(self.handles.values())[1:]):
            if not self.kernel.CloseHandle(handle):
                failed = True
        self.handles.clear()
        self.ancestors.clear()
        if failed:
            raise _FileError("HANDLE_CLOSE_FAILED")


def _backend(root: Path) -> _WindowsIO:
    # Linux dir_fd pins an inode but cannot deny ancestor rename outside root.
    # Until an equivalent namespace guard is available, defer that file entry.
    if os.name != "nt":
        raise _FileError("FS_CAPABILITY_UNAVAILABLE")
    try:
        return _WindowsIO(root)
    except _FileError:
        raise
    except (AttributeError, NotImplementedError, ValueError):
        raise _FileError("FS_CAPABILITY_UNAVAILABLE") from None
