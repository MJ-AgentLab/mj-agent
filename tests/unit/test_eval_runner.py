"""Synthetic-only CLI acceptance. Fixed outcomes are never sampled runtime evidence."""

from __future__ import annotations

import builtins
import ctypes
import hashlib
import json
import os
import socket
import subprocess
import sys
from importlib import import_module
from inspect import signature
from pathlib import Path
from typing import Any, get_type_hints
from unittest.mock import Mock

import pytest

from mj_agent.evaluation import _file_io as fio
from mj_agent.evaluation import runner
from mj_agent.evaluation.core import replay
from mj_agent.evaluation.schema import ReplayInputs

FIXTURES = Path(__file__).parent / "fixtures" / "eval_core"
BASELINE = Path(__file__).parent / "fixtures/eval_cli/baseline.synthetic.json"
EXPECTED = json.loads((Path(__file__).parent / "fixtures/eval_cli/expected.json").read_bytes())
FILES = {"config": "config.json", "dataset": "dataset.jsonl", "observations": "observations.jsonl",
         "manifest": "manifest.json", "reference": "reference.json", "reviews": "reviews.jsonl"}
OPTIONS = {"config": "--eval-config", "dataset": "--dataset", "observations": "--observations",
           "manifest": "--manifest", "reference": "--reference", "reviews": "--reviews"}


def _inspection_module() -> Any:
    return import_module("mj_agent.evaluation.inspection_runner")


def _inspection_main(args: list[str], root: Path) -> int:
    return int(_inspection_module().main(args, repo_root=root))


def _arguments(directory: Path, output: Path, *, reviews: bool = True) -> list[str]:
    args = ["--synthetic-fixture"]
    for field, filename in FILES.items():
        if field != "reviews" or reviews:
            args.extend([OPTIONS[field], str(directory / filename)])
    return [*args, "--output-dir", str(output)]


def _replace(args: list[str], option: str, value: str) -> None:
    args[args.index(option) + 1] = value


def _main(args: list[str], root: Path) -> int:
    return runner.main(args, repo_root=root)


def _reject(*args: Any, **kwargs: Any) -> Any:
    raise AssertionError("forbidden operation")


@pytest.fixture
def inputs_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "inputs"
    directory.mkdir()
    for filename in FILES.values():
        (directory / filename).write_bytes((FIXTURES / filename).read_bytes())
    return directory


def test_public_cli_signature() -> None:
    main = runner.main
    assert list(signature(main).parameters) == ["argv", "repo_root"]
    assert signature(main).parameters["argv"].default is None
    assert signature(main).parameters["repo_root"].kind.name == "KEYWORD_ONLY"
    assert get_type_hints(main) == {"argv": list[str] | None, "repo_root": Path | None, "return": int}


@pytest.mark.parametrize("option", ["missing_mode", "baseline_missing_value", "--actual", "--profile", "--runtime-observation"])
def test_unavailable_mode_and_options_are_refused_before_io(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, option: str,
) -> None:
    args = _arguments(inputs_dir, tmp_path / "output")
    if option == "missing_mode":
        args.remove("--synthetic-fixture")
    elif option == "baseline_missing_value":
        args.append("--baseline")
    else:
        args.extend([option, "do-not-echo"])
    backend = Mock(side_effect=_reject)
    core = Mock(side_effect=_reject)
    monkeypatch.setattr(runner, "_backend", backend)
    monkeypatch.setattr(runner, "replay", core)
    assert _main(args, tmp_path) == EXPECTED["invalid_exit"]
    backend.assert_not_called()
    core.assert_not_called()


@pytest.mark.parametrize("source", ["runtime_observation", "unknown", None])
@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_source_gate_reads_only_manifest_before_replay_or_other_inputs(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], source: str | None,
) -> None:
    manifest = json.loads((inputs_dir / "manifest.json").read_bytes())
    manifest["source_kind"] = source
    (inputs_dir / "manifest.json").write_bytes(json.dumps(manifest).encode())
    backend = fio._WindowsIO
    original = backend.read
    seen = []

    def manifest_only(self: Any, parts: tuple[str, ...]) -> bytes:
        seen.append(parts)
        assert parts == ("inputs", "manifest.json")
        return original(self, parts)

    monkeypatch.setattr(backend, "read", manifest_only)
    monkeypatch.setattr(runner, "replay", _reject)
    output = tmp_path / "output"
    args = [*_arguments(inputs_dir, output), "--baseline", str(tmp_path / "must-not-read.json")]
    assert _main(args, tmp_path) == 2
    assert seen == [("inputs", "manifest.json")]
    diagnostic = json.loads(capsys.readouterr().err)
    assert diagnostic["reason_code"] == ("ACTUAL_ENTRY_DEFERRED" if source == "runtime_observation"
                                         else "SOURCE_KIND_INVALID")
    assert not output.exists()


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_synthetic_cli_matches_core_and_fixed_outcomes_with_deterministic_bytes(
    inputs_dir: Path, tmp_path: Path,
) -> None:
    inputs = ReplayInputs(**{field: (inputs_dir / filename).read_bytes() for field, filename in FILES.items()})
    fixed_cases = json.loads((FIXTURES / "expected.json").read_bytes())["case_statuses"]
    for name in ("first", "second"):
        output = tmp_path / name
        assert _main(_arguments(inputs_dir, output), tmp_path) == EXPECTED["synthetic_exit"]
        report = json.loads((output / "report.json").read_bytes())
        assert report == replay(inputs)
        assert {c["case_id"]: c["status"] for c in report["cases"]} == fixed_cases
        assert report["counts"]["judged_cases"] == report["counts"]["planned_cases"] == EXPECTED["planned_cases"]
        assert report["measurement"]["status"] == EXPECTED["measurement"]
        assert report["measurement"]["metrics"] is EXPECTED["runtime_metrics"]
        assert report["baseline_eligible"] is EXPECTED["baseline_eligible"]
        assert EXPECTED["core_limit"] in report["limitations"]
        assert (output / "report.md").read_bytes() == report["markdown"].encode()
    for filename in ("report.json", "report.md"):
        first = (tmp_path / "first" / filename).read_bytes()
        assert first == (tmp_path / "second" / filename).read_bytes()
        assert b"\r" not in first


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_relative_paths_and_optional_reviews_preserve_gaps(inputs_dir: Path, tmp_path: Path) -> None:
    args = _arguments(Path("inputs"), Path("output"), reviews=False)
    assert _main(args, tmp_path) == 3
    report = json.loads((tmp_path / "output/report.json").read_bytes())
    assert report["counts"]["review_required_cases"] > 0
    assert report["counts"]["planned_cases"] == 22


@pytest.mark.parametrize("target", ["empty_directory", "report.json", "report.md", "input"])
@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_existing_output_never_overwrites_or_removes_files(
    inputs_dir: Path, tmp_path: Path, target: str,
) -> None:
    output = inputs_dir if target == "input" else tmp_path / "output"
    if target != "input":
        output.mkdir()
    if target in {"report.json", "report.md"}:
        (output / target).write_bytes(b"preserve evidence")
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    assert _main(_arguments(inputs_dir, output), tmp_path) == 2
    assert {p.name: p.read_bytes() for p in output.iterdir()} == before


@pytest.mark.parametrize("path", [
    "https://example.invalid/do-not-echo", "file:///private", "s3://bucket/key",
    r"\\server\share\input.json", "//server/share/input.json", r"\\?\C:\private\input.json",
    ".env.production", "config/secrets-mcp.enc", ".ssh/id_rsa", "credentials.json",
    "private.pem", "client.key", "tokens.json", "config.json:stream", "../outside.json",
    r"C:relative.json",
])
@pytest.mark.parametrize("option", ["--eval-config", "--output-dir", "--baseline"])
def test_unsafe_paths_are_rejected_before_metadata_or_reads_without_echo(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], path: str, option: str,
) -> None:
    args = _arguments(inputs_dir, tmp_path / "output")
    if option == "--baseline":
        args.extend([option, path])
    else:
        _replace(args, option, path)
    backend = Mock(side_effect=_reject)
    monkeypatch.setattr(runner, "_backend", backend)
    assert _main(args, tmp_path) == 2
    backend.assert_not_called()
    captured = capsys.readouterr()
    assert path not in captured.err + captured.out
    assert "INPUT_INVALID" in captured.err


@pytest.mark.skipif(os.name != "nt", reason="Windows native alias rules")
@pytest.mark.parametrize("alias", ["credentials.json ", "config/secrets-test.enc.", ".ssh./id_rsa.",
                                  "client.key.", "ordinary.json.", "ordinary.json ", "parent./input.json",
                                  "NUL", "COM1.json", "LPT¹", "CREDEN~1.JSON"])
@pytest.mark.parametrize("option", ["--eval-config", "--output-dir", "--baseline"])
def test_windows_aliases_are_rejected_before_backend(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, alias: str, option: str,
) -> None:
    args = _arguments(inputs_dir, tmp_path / "output")
    if option == "--baseline":
        args.extend([option, alias])
    else:
        _replace(args, option, alias)
    backend = Mock(side_effect=_reject)
    monkeypatch.setattr(runner, "_backend", backend)
    assert _main(args, tmp_path) == 2
    backend.assert_not_called()


def test_absolute_escape_and_relative_root_are_refused_before_io(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = _arguments(inputs_dir, tmp_path / "output")
    _replace(args, "--reference", str(tmp_path.parent / "outside.json"))
    backend = Mock(side_effect=_reject)
    monkeypatch.setattr(runner, "_backend", backend)
    assert _main(args, tmp_path) == 2
    assert _main(_arguments(inputs_dir, tmp_path / "output"), Path("relative")) == 2
    backend.assert_not_called()


@pytest.mark.parametrize("defect", ["missing", "directory", "size", "invalid_json", "utf8", "hash"])
@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_invalid_input_has_safe_diagnostics(inputs_dir: Path, tmp_path: Path,
                                           capsys: pytest.CaptureFixture[str], defect: str) -> None:
    args = _arguments(inputs_dir, tmp_path / "output")
    marker = b"do-not-echo-private-payload"
    if defect == "missing":
        _replace(args, "--eval-config", str(tmp_path / "missing.json"))
    elif defect == "directory":
        _replace(args, "--eval-config", str(inputs_dir))
    elif defect == "size":
        (inputs_dir / "config.json").write_bytes(b" " * (fio._MAX_BYTES + 1))
    elif defect == "hash":
        (inputs_dir / "observations.jsonl").write_bytes(b"")
    else:
        (inputs_dir / "config.json").write_bytes((b"\xff" if defect == "utf8" else b"") + marker)
    assert _main(args, tmp_path) == 2
    assert marker.decode() not in capsys.readouterr().err


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_hard_link_input_is_rejected_before_payload_read(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    alias = inputs_dir / "alias.json"
    os.link(inputs_dir / "config.json", alias)
    args = _arguments(inputs_dir, tmp_path / "output")
    _replace(args, "--eval-config", str(alias))
    original = os.fdopen
    links = []

    def guard(descriptor: int, mode: str, *a: Any, **kw: Any) -> Any:
        links.append(os.fstat(descriptor).st_nlink)
        return original(descriptor, mode, *a, **kw)

    monkeypatch.setattr(os, "fdopen", guard)
    assert _main(args, tmp_path) == 2
    assert not (tmp_path / "output").exists()
    assert links == [1]  # manifest only; hard-linked config is refused before stream construction


@pytest.mark.skipif(os.name != "nt", reason="Windows native handle metadata")
@pytest.mark.parametrize("target", ["root", "ancestor", "file"])
@pytest.mark.parametrize("attribute", [0x400, 0x1000, 0x400000])
def test_reparse_attributes_fail_before_file_read(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, target: str, attribute: int,
) -> None:
    original = fio._WindowsIO._prototypes
    suffix = str({"root": tmp_path, "ancestor": inputs_dir, "file": inputs_dir / "manifest.json"}[target])
    seen = []
    reads = []

    def prototypes(self: Any) -> None:
        original(self)
        get_info = self.kernel.GetFileInformationByHandle

        def reparse(handle: int, pointer: Any) -> int:
            result = get_info(handle, pointer)
            buffer = ctypes.create_unicode_buffer(4096)
            self.kernel.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
            if buffer.value.casefold().endswith(suffix.casefold()):
                ctypes.cast(pointer, ctypes.POINTER(fio._FileInfo)).contents.attributes |= attribute
                seen.append(True)
            return int(result)

        self.kernel.GetFileInformationByHandle = reparse

    monkeypatch.setattr(fio._WindowsIO, "_prototypes", prototypes)
    def reject_read(*args: Any, **kwargs: Any) -> Any:
        reads.append(True)
        return _reject(*args, **kwargs)

    monkeypatch.setattr(os, "fdopen", reject_read)
    assert _main(_arguments(inputs_dir, tmp_path / "output"), tmp_path) == 2
    assert seen
    assert not reads


@pytest.mark.skipif(os.name != "nt", reason="Windows native drive classification")
def test_network_drive_fails_closed_before_open(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = fio._WindowsIO._prototypes
    opened = Mock(side_effect=_reject)

    def prototypes(self: Any) -> None:
        original(self)
        self.kernel.GetDriveTypeW = lambda anchor: 4
        self.kernel.CreateFileW = opened

    monkeypatch.setattr(fio._WindowsIO, "_prototypes", prototypes)
    assert _main(_arguments(inputs_dir, tmp_path / "output"), tmp_path) == 2
    opened.assert_not_called()


@pytest.mark.skipif(os.name != "nt", reason="Windows shared-handle namespace lock")
def test_pinned_input_directory_cannot_be_replaced_during_replay(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = fio._WindowsIO.read
    attempted = []

    def read(self: Any, parts: tuple[str, ...]) -> bytes:
        result = original(self, parts)
        if parts[-1] == "manifest.json":
            # Both exact targets belong to this temporary fixture; no outside directory is moved.
            with pytest.raises(PermissionError):
                os.rename(inputs_dir, tmp_path / "renamed-inputs")
            attempted.append(True)
        return result

    monkeypatch.setattr(fio._WindowsIO, "read", read)
    assert _main(_arguments(inputs_dir, tmp_path / "output"), tmp_path) == 3
    assert attempted == [True]


@pytest.mark.skipif(os.name != "nt", reason="Windows file identity check")
def test_file_change_and_read_bound_are_enforced(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = fio._WindowsIO._info
    calls = []

    def changed(self: Any, handle: int) -> Any:
        info = original(self, handle)
        if self._final(handle).endswith("config.json"):
            calls.append(True)
            if len(calls) == 3:  # open guard, pre-read, post-read
                info.written_low ^= 1
        return info

    monkeypatch.setattr(fio._WindowsIO, "_info", changed)
    session = fio._backend(tmp_path)
    try:
        with pytest.raises(fio._FileError, match="FILE_CHANGED"):
            session.read(("inputs", "config.json"))
    finally:
        session.close()


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_bounded_read_never_requests_unlimited_bytes(inputs_dir: Path, tmp_path: Path,
                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    original = os.fdopen
    requested = []

    class Stream:
        def __init__(self, descriptor: int, mode: str, **kwargs: Any) -> None:
            self.stream = original(descriptor, mode, **kwargs)

        def __enter__(self) -> Stream:
            self.stream.__enter__()
            return self

        def read(self, size: int) -> bytes:
            requested.append(size)
            assert size == fio._MAX_BYTES + 1
            return b"x" * size

        def __exit__(self, *args: Any) -> Any:
            return self.stream.__exit__(*args)

    session = fio._backend(tmp_path)
    monkeypatch.setattr(os, "fdopen", Stream)
    try:
        with pytest.raises(fio._FileError, match="INPUT_SIZE_LIMIT"):
            session.read(("inputs", "config.json"))
    finally:
        session.close()
    assert requested == [fio._MAX_BYTES + 1]


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_missing_output_parent_is_not_created(inputs_dir: Path, tmp_path: Path) -> None:
    output = tmp_path / "missing-parent" / "output"
    assert _main(_arguments(inputs_dir, output), tmp_path) == 2
    assert not output.parent.exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows exclusive native create")
def test_second_write_failure_preserves_partial_output_and_safe_core_diagnostic(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    original = fio._WindowsIO._open

    def fail(self: Any, parent: int, name: str, **kwargs: Any) -> int:
        if name == "report.md" and kwargs.get("writing"):
            raise PermissionError("do-not-echo-private-os-error")
        return original(self, parent, name, **kwargs)

    monkeypatch.setattr(fio._WindowsIO, "_open", fail)
    output = tmp_path / "partial"
    assert _main(_arguments(inputs_dir, output), tmp_path) == 2
    assert (output / "report.json").is_file()
    assert not (output / "report.md").exists()
    diagnostic = json.loads(capsys.readouterr().err)
    assert diagnostic == {"core_exit_code": 3, "exit_code": 2, "input_status": "INPUT_INVALID",
                          "reason_code": "OUTPUT_IO_FAILED"}


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_close_failure_is_not_success(inputs_dir: Path, tmp_path: Path,
                                      monkeypatch: pytest.MonkeyPatch) -> None:
    backend = fio._WindowsIO
    original = backend.close

    def fail(self: Any) -> None:
        original(self)
        raise OSError("do-not-echo-close-error")

    monkeypatch.setattr(backend, "close", fail)
    assert _main(_arguments(inputs_dir, tmp_path / "output"), tmp_path) == 2


def test_missing_guard_capability_fails_closed_without_replay(inputs_dir: Path, tmp_path: Path,
                                                             monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(root: Path) -> Any:
        raise fio._FileError("FS_CAPABILITY_UNAVAILABLE")

    monkeypatch.setattr(runner, "_backend", unavailable)
    monkeypatch.setattr(runner, "replay", _reject)
    assert _main(_arguments(inputs_dir, tmp_path / "output"), tmp_path) == 2
    assert not (tmp_path / "output").exists()


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_baseline_raw_bytes_are_forwarded_once_without_enabling_comparison(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = BASELINE.read_bytes() + b" \r\n"
    baseline = inputs_dir / "baseline.json"
    baseline.write_bytes(raw)
    core = Mock(wraps=replay)
    monkeypatch.setattr(runner, "replay", core)
    original = fio._WindowsIO.read
    reads = []

    def read(self: Any, parts: tuple[str, ...]) -> bytes:
        reads.append(parts)
        return original(self, parts)

    monkeypatch.setattr(fio._WindowsIO, "read", read)
    for name, extra in (("without", []), ("with", ["--baseline", str(baseline)])):
        assert _main([*_arguments(inputs_dir, tmp_path / name), *extra], tmp_path) == 3
    assert core.call_count == 2
    assert core.call_args_list[0].args[0].baseline == b""
    assert core.call_args_list[1].args[0].baseline == raw
    assert reads.count(("inputs", "baseline.json")) == 1
    assert reads[0] == reads[len(FILES)] == ("inputs", "manifest.json")
    for filename in ("report.json", "report.md"):
        assert (tmp_path / "with" / filename).read_bytes() == (tmp_path / "without" / filename).read_bytes()
    report = json.loads((tmp_path / "with/report.json").read_bytes())
    assert report["regression"]["status"] == "NOT_EVALUATED"
    assert report["measurement"]["metrics"] is None
    assert report["baseline_eligible"] is False


@pytest.mark.parametrize("raw, reason", [
    (b"", "BASELINE_INPUT_EMPTY"), (b" ", "INVALID_INPUT_SCHEMA"),
    (b"null", "BASELINE_NOT_OBJECT"), (b"[]", "BASELINE_NOT_OBJECT"),
    (b'"do-not-echo"', "BASELINE_NOT_OBJECT"), (b"0", "BASELINE_NOT_OBJECT"),
    (b"false", "BASELINE_NOT_OBJECT"), (b"do-not-echo", "INVALID_INPUT_SCHEMA"),
    (b"\xff", "INVALID_INPUT_SCHEMA"),
    (b'{"a":1,"a":2}', "DUPLICATE_JSON_KEY"), (b'{"a":NaN}', "NON_FINITE_JSON"),
    (b'{"a":' + b"[" * 33 + b"0" + b"]" * 33 + b"}", "JSON_DEPTH_LIMIT"),
])
@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_invalid_baseline_is_refused_before_replay_or_output(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], raw: bytes, reason: str,
) -> None:
    baseline = inputs_dir / "baseline.json"
    baseline.write_bytes(raw)
    core = Mock(side_effect=_reject)
    monkeypatch.setattr(runner, "replay", core)
    output = tmp_path / "output"
    assert _main([*_arguments(inputs_dir, output), "--baseline", str(baseline)], tmp_path) == 2
    core.assert_not_called()
    assert not output.exists()
    error = capsys.readouterr().err
    assert json.loads(error) == {"input_status": "INPUT_INVALID", "exit_code": 2, "reason_code": reason}
    assert "do-not-echo" not in error and str(baseline) not in error


@pytest.mark.parametrize("defect", ["missing", "directory", "too_large", "hard_link"])
@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_baseline_uses_existing_native_file_guards(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], defect: str,
) -> None:
    baseline = inputs_dir / "baseline.json"
    if defect == "directory":
        baseline.mkdir()
    elif defect == "too_large":
        baseline.write_bytes(b" " * (fio._MAX_BYTES + 1))
    elif defect == "hard_link":
        original = inputs_dir / "baseline-original.json"
        original.write_bytes(BASELINE.read_bytes())
        os.link(original, baseline)
    core = Mock(side_effect=_reject)
    monkeypatch.setattr(runner, "replay", core)
    original_open = os.fdopen
    streams = []

    def open_stream(descriptor: int, mode: str, *args: Any, **kwargs: Any) -> Any:
        streams.append(os.fstat(descriptor).st_size)
        return original_open(descriptor, mode, *args, **kwargs)

    monkeypatch.setattr(os, "fdopen", open_stream)
    output = tmp_path / "output"
    assert _main([*_arguments(inputs_dir, output), "--baseline", str(baseline)], tmp_path) == 2
    core.assert_not_called()
    assert len(streams) == len(FILES)  # no stream was constructed for the refused baseline
    assert not output.exists()
    assert str(baseline) not in capsys.readouterr().err


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
@pytest.mark.parametrize("defect", ["reparse", "offline", "recall", "changed"])
def test_baseline_handle_metadata_prevents_replay(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], defect: str,
) -> None:
    baseline = inputs_dir / "baseline.json"
    baseline.write_bytes(BASELINE.read_bytes())
    original = fio._WindowsIO._prototypes
    checked = []

    def prototypes(self: Any) -> None:
        original(self)
        get_info = self.kernel.GetFileInformationByHandle

        def info(handle: int, pointer: Any) -> int:
            result = get_info(handle, pointer)
            if self._final(handle).endswith("baseline.json"):
                checked.append(True)
                metadata = ctypes.cast(pointer, ctypes.POINTER(fio._FileInfo)).contents
                if defect == "changed":
                    if len(checked) == 3:
                        metadata.written_low ^= 1
                else:
                    metadata.attributes |= {"reparse": 0x400, "offline": 0x1000, "recall": 0x400000}[defect]
            return int(result)

        self.kernel.GetFileInformationByHandle = info

    monkeypatch.setattr(fio._WindowsIO, "_prototypes", prototypes)
    core = Mock(side_effect=_reject)
    monkeypatch.setattr(runner, "replay", core)
    output = tmp_path / "output"
    assert _main([*_arguments(inputs_dir, output), "--baseline", str(baseline)], tmp_path) == 2
    assert checked
    assert core.call_count == 0
    assert not output.exists()
    diagnostic = json.loads(capsys.readouterr().err)
    assert diagnostic["reason_code"] == ("FILE_CHANGED" if defect == "changed" else "SPECIAL_FILE_PATH_FORBIDDEN")


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_baseline_at_file_size_limit_stays_selftest(inputs_dir: Path, tmp_path: Path) -> None:
    baseline = inputs_dir / "baseline.json"
    baseline.write_bytes(b"{}" + b" " * (fio._MAX_BYTES - 2))
    assert _main([*_arguments(inputs_dir, tmp_path / "output"), "--baseline", str(baseline)], tmp_path) == 3
    report = json.loads((tmp_path / "output/report.json").read_bytes())
    assert report["regression"]["status"] == "NOT_EVALUATED"


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_real_baseline_process_is_deterministic_and_offline(inputs_dir: Path, tmp_path: Path) -> None:
    baseline = inputs_dir / "baseline.json"
    baseline.write_bytes(BASELINE.read_bytes())
    for name in ("without", "with", "repeat"):
        args = _arguments(inputs_dir, tmp_path / name)
        if name != "without":
            args.extend(["--baseline", str(baseline)])
        completed = _process(args, tmp_path, sentinels=True)
        assert completed.returncode == 3, completed.stderr
        assert completed.stderr == b""
    for filename in ("report.json", "report.md"):
        assert (tmp_path / "without" / filename).read_bytes() == (tmp_path / "with" / filename).read_bytes()
        assert (tmp_path / "with" / filename).read_bytes() == (tmp_path / "repeat" / filename).read_bytes()


_BOOTSTRAP = """
import builtins, os, pathlib, runpy, socket
original_import = builtins.__import__
def import_guard(name, *args, **kwargs):
    if name.startswith(('mj_agent.config', 'mj_agent.agent', 'mj_agent.tools', 'dotenv', 'psycopg', 'openai')):
        raise AssertionError('application import forbidden')
    return original_import(name, *args, **kwargs)
def reject(*args, **kwargs):
    raise AssertionError('network forbidden')
original_open = builtins.open
def safe_open(file, *args, **kwargs):
    if isinstance(file, (str, os.PathLike)):
        name = pathlib.Path(file).name.casefold()
        if name.startswith('.env') or (name.startswith('secrets') and name.endswith('.enc')):
            raise AssertionError('secret read forbidden')
    return original_open(file, *args, **kwargs)
builtins.__import__ = import_guard
builtins.open = safe_open
socket.socket.connect = reject
socket.socket.connect_ex = reject
socket.create_connection = reject
runpy.run_module('mj_agent.evaluation.runner', run_name='__main__')
"""


def _process(args: list[str], root: Path, *, sentinels: bool = False) -> subprocess.CompletedProcess[bytes]:
    # Only non-secret platform values enter the child. No ambient API keys or dotenv loading.
    env = {name: os.environ[name] for name in ("PATH", "SYSTEMROOT", "WINDIR", "PATHEXT")
           if name in os.environ}
    env.update(PYTHONPATH=str(Path(__file__).parents[2] / "src"), PYTHONNOUSERSITE="1",
               PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0", TEMP=str(root), TMP=str(root))
    entry = ["-c", _BOOTSTRAP] if sentinels else ["-m", "mj_agent.evaluation.runner"]
    return subprocess.run([sys.executable, "-B", "-X", "utf8", *entry, *args], cwd=root,
                          env=env, capture_output=True, check=False, timeout=30)


@pytest.mark.parametrize("mode, expected", [("synthetic", 3), ("help", 0), ("empty", 2),
                                          ("unknown", 2), ("actual", 2), ("baseline", 2)])
@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_real_module_process_exit_and_closed_environment(
    inputs_dir: Path, tmp_path: Path, mode: str, expected: int,
) -> None:
    args = _arguments(inputs_dir, tmp_path / "output")
    if mode == "help":
        args = ["--help"]
    elif mode == "empty":
        args = []
    elif mode == "unknown":
        args = ["--unknown=do-not-echo"]
    elif mode == "baseline":
        args.extend(["--baseline", "do-not-echo"])
    elif mode == "actual":
        manifest = json.loads((inputs_dir / "manifest.json").read_bytes())
        manifest["source_kind"] = "runtime_observation"
        (inputs_dir / "manifest.json").write_bytes(json.dumps(manifest).encode())
    completed = _process(args, tmp_path)
    assert completed.returncode == expected
    assert b"do-not-echo" not in completed.stderr
    assert (tmp_path / "output/report.json").exists() is (mode == "synthetic")


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_real_child_process_blocks_application_imports_secret_reads_and_network(
    inputs_dir: Path, tmp_path: Path,
) -> None:
    completed = _process(_arguments(inputs_dir, tmp_path / "output"), tmp_path, sentinels=True)
    assert completed.returncode == 3, completed.stderr


@pytest.mark.parametrize("baseline", [False, True])
@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_confirmed_synthetic_red_line_failure_returns_six_in_real_process(
    inputs_dir: Path, tmp_path: Path, baseline: bool,
) -> None:
    rows = [json.loads(line) for line in (inputs_dir / "observations.jsonl").read_bytes().splitlines()]
    target = next(row for row in rows if row["case_id"] == "RL-05")
    target["tool_calls"] = [{"sequence": 1, "call_id": "blocked", "tool_name": "execute_sql",
                             "sql": "SELECT 1; DROP TABLE forbidden", "outcome": "error",
                             "error_codes": ["blocked"]}]
    raw = b"\n".join(json.dumps(row).encode() for row in rows) + b"\n"
    manifest = json.loads((inputs_dir / "manifest.json").read_bytes())
    manifest["hashes"]["observations"] = hashlib.sha256(raw).hexdigest()
    (inputs_dir / "observations.jsonl").write_bytes(raw)
    (inputs_dir / "manifest.json").write_bytes(json.dumps(manifest).encode())
    args = _arguments(inputs_dir, tmp_path / "output")
    if baseline:
        path = inputs_dir / "baseline.json"
        path.write_bytes(BASELINE.read_bytes())
        args.extend(["--baseline", str(path)])
    completed = _process(args, tmp_path, sentinels=True)
    assert completed.returncode == EXPECTED["red_line_exit"]
    report = json.loads((tmp_path / "output/report.json").read_bytes())
    assert report["safety"]["status"] == "SELFTEST_HARD_FAIL"
    assert report["measurement"]["metrics"] is None


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
def test_in_process_does_not_import_application_or_connect(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = builtins.__import__

    def guard(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.startswith(("mj_agent.config", "mj_agent.agent", "mj_agent.tools", "dotenv", "psycopg", "openai")):
            raise AssertionError("application import forbidden")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guard)
    monkeypatch.setattr(socket.socket, "connect", _reject)
    monkeypatch.setattr(socket, "create_connection", _reject)
    assert _main(_arguments(inputs_dir, tmp_path / "output"), tmp_path) == 3


def test_non_windows_entry_is_explicitly_deferred_without_any_local_open(monkeypatch: pytest.MonkeyPatch) -> None:
    root = Path.cwd()
    monkeypatch.setattr(fio.os, "name", "posix")
    monkeypatch.setattr(fio, "_WindowsIO", _reject)
    with pytest.raises(fio._FileError, match="FS_CAPABILITY_UNAVAILABLE"):
        fio._backend(root)


@pytest.mark.skipif(os.name != "nt", reason="Windows native descriptor ownership")
def test_stream_construction_failure_releases_input_descriptor(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    descriptors = []

    def fail(descriptor: int, *args: Any, **kwargs: Any) -> Any:
        descriptors.append(descriptor)
        raise OSError("stream creation failed")

    monkeypatch.setattr(os, "fdopen", fail)
    assert _main(_arguments(inputs_dir, tmp_path / "output"), tmp_path) == 2
    assert len(descriptors) == 1
    with pytest.raises(OSError):
        os.fstat(descriptors[0])


def test_inspection_cli_public_signature_and_help(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _inspection_module()
    assert list(signature(module.main).parameters) == ["argv", "repo_root"]
    assert signature(module.main).parameters["repo_root"].kind.name == "KEYWORD_ONLY"
    assert get_type_hints(module.main) == {"argv": list[str] | None, "repo_root": Path | None, "return": int}
    backend = Mock(side_effect=_reject)
    monkeypatch.setattr(module, "_backend", backend)
    assert module.main(["--help"]) == 0
    backend.assert_not_called()


@pytest.mark.parametrize("mode", ["missing", "--actual", "--profile", "--runtime-observation", "abbreviation"])
def test_inspection_cli_mode_refuses_before_io(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _inspection_module()
    args = _arguments(inputs_dir, tmp_path / "output")
    if mode == "missing":
        args.remove("--synthetic-fixture")
    elif mode == "abbreviation":
        args[0] = "--synthetic"
    else:
        args.extend([mode, "must-not-echo"])
    backend = Mock(side_effect=_reject)
    inspector = Mock(side_effect=_reject)
    monkeypatch.setattr(module, "_backend", backend)
    monkeypatch.setattr(module, "inspect_source", inspector)
    assert module.main(args, repo_root=tmp_path) == 2
    backend.assert_not_called()
    inspector.assert_not_called()
    error = capsys.readouterr().err
    assert json.loads(error)["reason_code"] == "CLI_ARGUMENT_INVALID"
    assert "must-not-echo" not in error and not (tmp_path / "output").exists()


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native inspection deferred")
@pytest.mark.parametrize("source", ["runtime_observation", "unknown", None])
def test_inspection_cli_manifest_only_gate(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source: str | None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _inspection_module()
    path = inputs_dir / "manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest["source_kind"] = source
    manifest["provenance"]["source_ref"] = "unit-condition-only-not-runtime-evidence"
    path.write_bytes(json.dumps(manifest).encode())
    original = fio._WindowsIO.read
    reads = []

    def manifest_only(self: Any, parts: tuple[str, ...]) -> bytes:
        reads.append(parts)
        assert parts == ("inputs", "manifest.json")
        return original(self, parts)

    inspector = Mock(side_effect=_reject)
    writer = Mock(side_effect=_reject)
    monkeypatch.setattr(fio._WindowsIO, "read", manifest_only)
    monkeypatch.setattr(fio._WindowsIO, "write", writer)
    monkeypatch.setattr(module, "inspect_source", inspector)
    args = [*_arguments(inputs_dir, tmp_path / "output"), "--baseline", str(tmp_path / "unread.json")]
    assert module.main(args, repo_root=tmp_path) == 2
    assert reads == [("inputs", "manifest.json")]
    inspector.assert_not_called()
    writer.assert_not_called()
    assert json.loads(capsys.readouterr().err)["reason_code"] == (
        "ACTUAL_ENTRY_DEFERRED" if source == "runtime_observation" else "SOURCE_KIND_INVALID")
    assert not (tmp_path / "output").exists()


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native inspection deferred")
@pytest.mark.parametrize("baseline", [False, True])
def test_inspection_cli_fixed_single_json_and_raw_inputs(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, baseline: bool,
) -> None:
    module = _inspection_module()
    original = module.inspect_source
    supplied = []
    snapshots = {field: (inputs_dir / filename).read_bytes() for field, filename in FILES.items()}
    baseline_raw = BASELINE.read_bytes() if baseline else b""
    if baseline:
        (inputs_dir / "baseline.json").write_bytes(baseline_raw)

    def inspect(inputs: ReplayInputs) -> dict[str, Any]:
        supplied.append(inputs)
        return original(inputs)

    monkeypatch.setattr(module, "inspect_source", inspect)
    outputs = []
    for name in ("first", "second"):
        output = tmp_path / name
        args = _arguments(inputs_dir, output)
        if baseline:
            args.extend(["--baseline", str(inputs_dir / "baseline.json")])
        assert module.main(args, repo_root=tmp_path) == 3
        assert sorted(p.name for p in output.iterdir()) == ["inspection.json"]
        outputs.append((output / "inspection.json").read_bytes())
    expected = json.loads((FIXTURES / "inspection.expected.json").read_bytes())
    assert outputs[0] == outputs[1] and outputs[0].endswith(b"\n") and b"\r" not in outputs[0]
    assert json.loads(outputs[0]) == expected
    assert len(supplied) == 2
    for inputs in supplied:
        assert all(getattr(inputs, field) == raw for field, raw in snapshots.items())
        assert inputs.baseline == baseline_raw
    assert all((inputs_dir / FILES[field]).read_bytes() == raw for field, raw in snapshots.items())


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native inspection deferred")
@pytest.mark.parametrize("gap", ["missing", "no_reviews", "stale", "unknown", "negative", "unknown_check"])
def test_inspection_cli_preserves_gaps_without_judging(
    inputs_dir: Path, tmp_path: Path, gap: str,
) -> None:
    manifest_path = inputs_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    args = _arguments(inputs_dir, tmp_path / "output", reviews=gap != "no_reviews")
    if gap in {"missing", "unknown"}:
        rows = [json.loads(line) for line in (inputs_dir / "observations.jsonl").read_bytes().splitlines()]
        if gap == "missing":
            rows = [row for row in rows if row["case_id"] != "HP-01"]
        else:
            rows[0]["tool_calls"][0]["outcome"] = "unknown"
        raw = b"\n".join(json.dumps(row).encode() for row in rows) + b"\n"
        (inputs_dir / "observations.jsonl").write_bytes(raw)
        manifest["hashes"]["observations"] = hashlib.sha256(raw).hexdigest()
    elif gap in {"stale", "negative"}:
        rows = [json.loads(line) for line in (inputs_dir / "reviews.jsonl").read_bytes().splitlines()]
        rows[0]["run_id" if gap == "stale" else "verdict"] = "stale-run" if gap == "stale" else "FAIL"
        (inputs_dir / "reviews.jsonl").write_bytes(b"\n".join(json.dumps(row).encode() for row in rows) + b"\n")
    elif gap == "unknown_check":
        rows = [json.loads(line) for line in (inputs_dir / "dataset.jsonl").read_bytes().splitlines()]
        rows[0]["expected_output"]["unknown_inspection_only_check"] = True
        raw = b"\n".join(json.dumps(row).encode() for row in rows) + b"\n"
        (inputs_dir / "dataset.jsonl").write_bytes(raw)
        manifest["hashes"]["dataset"] = hashlib.sha256(raw).hexdigest()
    manifest_path.write_bytes(json.dumps(manifest).encode())
    assert _inspection_main(args, tmp_path) == 3
    result = json.loads((tmp_path / "output/inspection.json").read_bytes())
    assert result["input_status"] == "VALID"
    assert result["coherence_status"] == ("INCOMPLETE" if gap in {"missing", "stale", "unknown"} else "CONSISTENT")
    assert result["counts"]["planned_cases"] == 22
    if gap == "missing":
        assert result["counts"]["observed_cases"] == 21
        assert result["gaps"]["missing_observations"] == ["HP-01"]
    if gap == "no_reviews":
        assert result["counts"]["provided_reviews"] == result["counts"]["bound_reviews"] == 0
    assert result["source_evidence_status"] == result["target_evidence_status"] == "UNVERIFIED"
    assert result["review_coverage_status"] == "NOT_CHECKED"
    assert result["runtime_metrics"] is None and result["baseline_eligible"] is False
    assert not {"cases", "measurement", "safety", "regression", "markdown"} & result.keys()


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native inspection deferred")
@pytest.mark.parametrize("raw, reason", [(b"", "BASELINE_INPUT_EMPTY"), (b"null", "BASELINE_NOT_OBJECT"),
    (b"[]", "BASELINE_NOT_OBJECT"), (b"1", "BASELINE_NOT_OBJECT"), (b"{", "INVALID_INPUT_SCHEMA"),
    (b'{"x":1,"x":2}', "DUPLICATE_JSON_KEY"), (b'{"x":NaN}', "NON_FINITE_JSON")],
    ids=["empty", "null", "array", "number", "json", "duplicate", "nan"])
def test_inspection_cli_invalid_baseline_never_inspects_or_writes(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], raw: bytes, reason: str,
) -> None:
    module = _inspection_module()
    (inputs_dir / "baseline.json").write_bytes(raw)
    inspector = Mock(side_effect=_reject)
    writer = Mock(side_effect=_reject)
    monkeypatch.setattr(module, "inspect_source", inspector)
    monkeypatch.setattr(fio._WindowsIO, "write", writer)
    args = [*_arguments(inputs_dir, tmp_path / "output"), "--baseline", str(inputs_dir / "baseline.json")]
    assert module.main(args, repo_root=tmp_path) == 2
    inspector.assert_not_called()
    writer.assert_not_called()
    assert json.loads(capsys.readouterr().err)["reason_code"] == reason
    assert not (tmp_path / "output").exists()


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native inspection deferred")
def test_inspection_cli_invalid_api_result_has_no_output(
    inputs_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = json.loads((inputs_dir / "manifest.json").read_bytes())
    manifest["hashes"]["dataset"] = "0" * 64
    (inputs_dir / "manifest.json").write_bytes(json.dumps(manifest).encode())
    assert _inspection_main(_arguments(inputs_dir, tmp_path / "output"), tmp_path) == 2
    diagnostic = json.loads(capsys.readouterr().err)
    assert diagnostic["reason_code"] == "INPUT_HASH_MISMATCH"
    assert "inspection_exit_code" not in diagnostic
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("field", ["--eval-config", "--manifest", "--reviews", "--baseline", "--output-dir"])
@pytest.mark.parametrize("value", [".env.production.", "NUL", "//server/share/x", "../escape.json",
                                   "https://invalid.example/never-read"])
def test_inspection_cli_paths_refuse_before_backend(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _inspection_module()
    args = _arguments(inputs_dir, tmp_path / "output")
    if field == "--baseline":
        args.extend([field, value])
    else:
        _replace(args, field, value)
    unsupported_reserved_name = value == "NUL" and os.name != "nt"
    backend = Mock(wraps=fio._backend) if unsupported_reserved_name else Mock(side_effect=_reject)
    inspector = Mock(side_effect=_reject)
    monkeypatch.setattr(module, "_backend", backend)
    monkeypatch.setattr(module, "inspect_source", inspector)
    assert module.main(args, repo_root=tmp_path) == 2
    diagnostic = json.loads(capsys.readouterr().err)
    if unsupported_reserved_name:
        backend.assert_called_once_with(tmp_path)
        assert diagnostic["reason_code"] == "FS_CAPABILITY_UNAVAILABLE"
    else:
        backend.assert_not_called()
    inspector.assert_not_called()
    assert value not in json.dumps(diagnostic)
    assert not (tmp_path / "output").exists()


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native inspection deferred")
@pytest.mark.parametrize("field", ["--eval-config", "--baseline"])
def test_inspection_cli_hardlink_is_refused_before_payload(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str,
) -> None:
    module = _inspection_module()
    alias = inputs_dir / "linked.json"
    os.link(inputs_dir / "config.json", alias)
    args = _arguments(inputs_dir, tmp_path / "output")
    if field == "--baseline":
        args.extend([field, str(alias)])
    else:
        _replace(args, field, str(alias))
    inspector = Mock(side_effect=_reject)
    monkeypatch.setattr(module, "inspect_source", inspector)
    assert module.main(args, repo_root=tmp_path) == 2
    inspector.assert_not_called()
    assert not (tmp_path / "output").exists()


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native inspection deferred")
@pytest.mark.parametrize("failure", ["collision", "parent", "write", "close"])
def test_inspection_cli_failed_delivery_preserves_output(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "output"
    if failure == "collision":
        output.mkdir()
        (output / "inspection.json").write_bytes(b"old-evidence")
    elif failure == "parent":
        output = tmp_path / "missing-parent/output"
    elif failure == "write":
        original = fio._WindowsIO.write

        def fail_write(self: Any, parts: tuple[str, ...], files: tuple[tuple[str, bytes], ...]) -> None:
            original(self, parts, files)
            raise OSError("must-not-echo")

        monkeypatch.setattr(fio._WindowsIO, "write", fail_write)
    else:
        original_close = fio._WindowsIO.close

        def fail_close(self: Any) -> None:
            original_close(self)
            raise fio._FileError("HANDLE_CLOSE_FAILED")

        monkeypatch.setattr(fio._WindowsIO, "close", fail_close)
    assert _inspection_main(_arguments(inputs_dir, output), tmp_path) == 2
    error = capsys.readouterr().err
    assert "must-not-echo" not in error
    assert json.loads(error)["inspection_exit_code"] == 3
    if failure == "collision":
        assert (output / "inspection.json").read_bytes() == b"old-evidence"
    elif failure == "parent":
        assert not output.parent.exists()
    else:
        assert json.loads((output / "inspection.json").read_bytes())["exit_code"] == 3


@pytest.mark.parametrize("platform", ["linux", "darwin"])
def test_inspection_cli_missing_platform_capability_refuses_before_reads(
    tmp_path: Path, inputs_dir: Path, monkeypatch: pytest.MonkeyPatch, platform: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _inspection_module()
    monkeypatch.setattr(fio.sys, "platform", platform)
    inspector = Mock(side_effect=_reject)
    monkeypatch.setattr(module, "inspect_source", inspector)
    assert module.main(_arguments(inputs_dir, tmp_path / "output"), repo_root=tmp_path) == 2
    inspector.assert_not_called()
    assert json.loads(capsys.readouterr().err)["reason_code"] == "FS_CAPABILITY_UNAVAILABLE"


_INSPECTION_BOOTSTRAP = """
import builtins, importlib.abc, os, pathlib, runpy, socket, sys
forbidden = ('mj_agent.evaluation.core', 'mj_agent.evaluation.judges', 'mj_agent.evaluation.report',
             'mj_agent.evaluation.runner', 'mj_agent.config', 'mj_agent.agent', 'mj_agent.tools',
             'dotenv', 'psycopg', 'openai')
events = []
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(forbidden):
            events.append('import')
            raise AssertionError('forbidden import')
sys.meta_path.insert(0, Guard())
def audit(event, args):
    if event in ('socket.connect', 'subprocess.Popen'):
        events.append('external')
        raise AssertionError('external operation forbidden')
    if event == 'open' and isinstance(args[0], (str, os.PathLike)):
        name = pathlib.Path(args[0]).name.casefold()
        if name.startswith('.env') or (name.startswith('secrets') and name.endswith('.enc')):
            events.append('secret')
            raise AssertionError('secret operation forbidden')
sys.addaudithook(audit)
try:
    runpy.run_module('mj_agent.evaluation.inspection_runner', run_name='__main__')
except SystemExit as exc:
    code = exc.code
assert not events, events
assert not any(name.startswith(forbidden) for name in sys.modules)
raise SystemExit(code)
"""


def _inspection_process(args: list[str], root: Path) -> subprocess.CompletedProcess[bytes]:
    env = {name: os.environ[name] for name in ("PATH", "SYSTEMROOT", "WINDIR", "PATHEXT")
           if name in os.environ}
    env.update(PYTHONPATH=str(Path(__file__).parents[2] / "src"), PYTHONNOUSERSITE="1",
               PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0", TEMP=str(root), TMP=str(root))
    return subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", _INSPECTION_BOOTSTRAP, *args],
                          cwd=root, env=env, capture_output=True, check=False, timeout=30)


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native inspection deferred")
def test_inspection_cli_fresh_process_is_offline_and_deterministic(inputs_dir: Path, tmp_path: Path) -> None:
    for name in ("first", "second"):
        completed = _inspection_process(_arguments(inputs_dir, tmp_path / name), tmp_path)
        assert completed.returncode == 3, completed.stderr
        assert completed.stdout == completed.stderr == b""
    assert (tmp_path / "first/inspection.json").read_bytes() == (tmp_path / "second/inspection.json").read_bytes()



@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native inspection deferred")
@pytest.mark.parametrize("target", ["root", "ancestor", "manifest"])
@pytest.mark.parametrize("attribute", [0x400, 0x1000, 0x400000])
def test_inspection_cli_native_attributes_refuse_before_read(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, target: str, attribute: int,
    capsys: pytest.CaptureFixture[str],
) -> None:
    suffix = str({"root": tmp_path, "ancestor": inputs_dir, "manifest": inputs_dir / "manifest.json"}[target])
    original = fio._WindowsIO._prototypes
    seen = []
    reader = Mock(side_effect=_reject)

    def prototypes(self: Any) -> None:
        original(self)
        get_info = self.kernel.GetFileInformationByHandle

        def attribute_info(handle: int, pointer: Any) -> int:
            result = get_info(handle, pointer)
            buffer = ctypes.create_unicode_buffer(4096)
            self.kernel.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
            if buffer.value.casefold().endswith(suffix.casefold()):
                ctypes.cast(pointer, ctypes.POINTER(fio._FileInfo)).contents.attributes |= attribute
                seen.append(True)
            return int(result)

        self.kernel.GetFileInformationByHandle = attribute_info

    monkeypatch.setattr(fio._WindowsIO, "_prototypes", prototypes)
    monkeypatch.setattr(os, "fdopen", reader)
    assert _inspection_main(_arguments(inputs_dir, tmp_path / "output"), tmp_path) == 2
    assert seen
    reader.assert_not_called()
    assert json.loads(capsys.readouterr().err)["reason_code"] == "SPECIAL_FILE_PATH_FORBIDDEN"


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native inspection deferred")
def test_inspection_cli_ancestor_lock_and_reference_non_access(
    inputs_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = json.loads((inputs_dir / "manifest.json").read_bytes())
    manifest["provenance"]["source_ref"] = ".env.never-resolve"
    manifest["provenance"]["sanitization_review_ref"] = "https://invalid.example/never-fetch"
    (inputs_dir / "manifest.json").write_bytes(json.dumps(manifest).encode())
    original = fio._WindowsIO.read
    seen = []
    locked = []

    def read(self: Any, parts: tuple[str, ...]) -> bytes:
        seen.append(parts)
        result = original(self, parts)
        if parts[-1] == "manifest.json":
            with pytest.raises(PermissionError):
                os.rename(inputs_dir, tmp_path / "replaced-inputs")
            locked.append(True)
        return result

    monkeypatch.setattr(fio._WindowsIO, "read", read)
    assert _inspection_main(_arguments(inputs_dir, tmp_path / "output"), tmp_path) == 3
    assert locked == [True]
    assert set(seen) == {("inputs", filename) for filename in FILES.values()}
    raw = (tmp_path / "output/inspection.json").read_bytes()
    assert b".env" not in raw and b"https://" not in raw


@pytest.mark.skipif(os.name != "nt", reason="SKIP_FS_CAPABILITY_UNAVAILABLE: native inspection deferred")
@pytest.mark.parametrize("case", ["rows", "duplicate", "sequence", "record_limit", "call_limit", "input_limit", "depth"])
def test_inspection_cli_invalid_payload_limits_have_no_output(
    inputs_dir: Path, tmp_path: Path, case: str, capsys: pytest.CaptureFixture[str],
) -> None:
    manifest_path = inputs_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    rows = [json.loads(line) for line in (inputs_dir / "observations.jsonl").read_bytes().splitlines()]
    if case == "rows":
        rows[0]["business_summary"] = "forbidden-synthetic-marker"
    elif case == "duplicate":
        rows.append(rows[0])
    elif case == "sequence":
        rows[0]["tool_calls"][0]["sequence"] = 9
    elif case == "record_limit":
        rows[0]["reply_excerpt"] = "x" * (256 * 1024)
    elif case == "call_limit":
        rows[0]["tool_calls"] = [dict(rows[0]["tool_calls"][0], sequence=i + 1, call_id=str(i))
                                  for i in range(101)]
    raw = b"\n".join(json.dumps(row).encode() for row in rows) + b"\n"
    if case == "input_limit":
        raw = b"x" * (10 * 1024 * 1024 + 1)
    if case == "depth":
        raw = b'{"x":' * 34 + b"0" + b"}" * 34 + b"\n"
    (inputs_dir / "observations.jsonl").write_bytes(raw)
    manifest["hashes"]["observations"] = hashlib.sha256(raw).hexdigest()
    manifest_path.write_bytes(json.dumps(manifest).encode())
    assert _inspection_main(_arguments(inputs_dir, tmp_path / "output"), tmp_path) == 2
    error = capsys.readouterr().err
    assert "forbidden-synthetic-marker" not in error and "inspection_exit_code" not in error
    assert not (tmp_path / "output").exists()
