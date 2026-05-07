"""Shared helpers for chart tools — backend / font / output path."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path

import matplotlib

# Force the non-interactive Agg backend so charts render headless
# (Chainlit / Docker / pytest).
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

_CN_FONT_CANDIDATES = (
    "Microsoft YaHei",
    "PingFang SC",
    "Source Han Sans CN",
    "Noto Sans CJK SC",
    "SimHei",
    "WenQuanYi Zen Hei",
)


def _cn_font_or_default() -> str:
    """Pick the first installed CJK-capable font; else matplotlib default."""
    available = {f.name for f in matplotlib.font_manager.fontManager.ttflist}
    for name in _CN_FONT_CANDIDATES:
        if name in available:
            return name
    return matplotlib.rcParams["font.family"][0]  # type: ignore[no-any-return]


def configure_style() -> None:
    """Set sensible rcParams once per process (Chinese font + minus sign)."""
    plt.rcParams["font.family"] = [_cn_font_or_default()]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 110
    plt.rcParams["savefig.dpi"] = 150
    plt.rcParams["savefig.bbox"] = "tight"


def chart_tmpdir() -> Path:
    """Resolve the chart output directory (env override or system tmp)."""
    override = os.environ.get("MJ_AGENT_CHART_TMPDIR")
    base = Path(override) if override else Path(tempfile.gettempdir()) / "mj-agent-charts"
    base.mkdir(parents=True, exist_ok=True)
    return base


def make_output_path(prefix: str, output_path: str | None) -> Path:
    """Resolve the chart PNG output path; auto-generate when None."""
    if output_path is not None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return chart_tmpdir() / f"{prefix}-{ts}.png"
