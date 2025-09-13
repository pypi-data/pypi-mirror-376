from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Optional

from ._slurm import (
    SlurmUnavailableError,
    normalize_state,
    require as _require,
    run as _run,
    sacct as _sacct,
    squeue as _squeue,
    sinfo as _sinfo,
    sprio as _sprio,
    sshare as _sshare,
    which as _which,
)
from .job import _TERMINAL


def node_state_counts() -> dict[str, int]:
    """Return a mapping of node state to count."""
    rows = _sinfo({"state": "%T", "count": "%D"}, runner=_run, which_func=_which)
    counts: Counter[str] = Counter()
    for r in rows:
        state = r.get("state", "")
        token = normalize_state(state)
        try:
            counts[token] += int(r.get("count", "0"))
        except ValueError:
            continue
    return dict(counts)


def recent_completions(span: str = "day", count: int = 7) -> list[tuple[str, int]]:
    """Return counts of recently completed jobs grouped by *span*."""
    if span not in {"day", "week"}:
        raise ValueError("span must be 'day' or 'week'")

    delta = timedelta(days=count if span == "day" else count * 7)
    start = (datetime.now() - delta).strftime("%Y-%m-%d")
    rows = _sacct(
        {"end": "End"},
        args=["--state=CD", f"--starttime={start}", "-X"],
        runner=_run,
        which_func=_which,
    )
    counts: Counter[str] = Counter()
    for r in rows:
        token = r.get("end", "").strip()
        if not token:
            continue
        try:
            dt = datetime.strptime(token.split(".")[0], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            continue
        if span == "week":
            year, week, _ = dt.isocalendar()
            key = f"{year}-W{week:02d}"
        else:
            key = dt.strftime("%Y-%m-%d")
        counts[key] += 1
    items = sorted(counts.items())
    return items[-count:]


def _parse_gpu(gres: str) -> int:
    total = 0
    for token in gres.split(","):
        token = token.strip().split("(")[0]
        if token.startswith("gpu:"):
            try:
                total += int(token.split(":")[-1])
            except ValueError:
                pass
    return total


def _partition_caps() -> dict[str, dict[str, int]]:
    rows = _sinfo(
        {"part": "%P", "cpus": "%C", "gres": "%G", "nodes": "%D"},
        args=["-a"],
        runner=_run,
        which_func=_which,
        check=False,
    )
    caps: dict[str, dict[str, int]] = {}
    for r in rows:
        part = r.get("part", "").rstrip("*")
        cpus = 0
        c_field = r.get("cpus", "")
        if c_field:
            try:
                cpus = int(c_field.split("/")[-1])
            except ValueError:
                pass
        gpus_per_node = _parse_gpu(r.get("gres", ""))
        nodes = 0
        d_field = r.get("nodes", "")
        if d_field:
            try:
                nodes = int(d_field)
            except ValueError:
                pass
        caps[part] = {"cpus": cpus, "gpus": gpus_per_node * nodes}
    return caps


def partition_utilization() -> dict[str, float]:
    """Return per-partition utilization percentage based on running jobs."""
    caps = _partition_caps()
    rows = _squeue(
        {"part": "%P", "cpus": "%C", "gres": "%b"},
        args=["-t", "RUNNING"],
        runner=_run,
        which_func=_which,
    )
    usage: dict[str, dict[str, int]] = {}
    for r in rows:
        part = r.get("part", "")
        c_field = r.get("cpus", "")
        cpus = 0
        if c_field:
            try:
                cpus = int(c_field)
            except ValueError:
                pass
        gpus = _parse_gpu(r.get("gres", ""))
        u = usage.setdefault(part, {"cpus": 0, "gpus": 0})
        u["cpus"] += cpus
        u["gpus"] += gpus
    utils: dict[str, float] = {}
    for part, cap in caps.items():
        use = usage.get(part, {})
        cpu_total = cap.get("cpus", 0)
        gpu_total = cap.get("gpus", 0)
        cpu_pct = use.get("cpus", 0) / cpu_total if cpu_total else 0.0
        gpu_pct = use.get("gpus", 0) / gpu_total if gpu_total else 0.0
        utils[part] = max(cpu_pct, gpu_pct) * 100
    return utils


def fairshare_scores() -> dict[str, float]:
    """Return a mapping of users to their fair-share scores."""
    rows: list[dict[str, str]]
    try:
        rows = _sprio({"user": "user", "fairshare": "fairshare"}, runner=_run, which_func=_which)
    except SlurmUnavailableError:
        try:
            rows = _sshare({"user": "user", "fairshare": "fairshare"}, runner=_run, which_func=_which)
        except SlurmUnavailableError:
            return {}

    scores: dict[str, float] = {}
    for r in rows:
        user = r.get("user", "")
        val = r.get("fairshare", "")
        try:
            scores[user] = float(val)
        except ValueError:
            continue
    return scores


def job_history() -> dict[str, dict[str, int]]:
    """Return per-user job completion statistics for the last 24 hours."""
    if not _which("sacct"):
        return {}

    now = datetime.now()
    start = now - timedelta(hours=24)
    rows = _sacct(
        {"user": "User", "state": "State"},
        args=[
            "-a",
            "-X",
            "-S",
            start.strftime("%Y-%m-%dT%H:%M:%S"),
            "-E",
            now.strftime("%Y-%m-%dT%H:%M:%S"),
        ],
        runner=_run,
        which_func=_which,
    )
    stats: dict[str, dict[str, int]] = {}
    for r in rows:
        user = r.get("user", "")
        state = r.get("state", "")
        if not user:
            continue
        token = normalize_state(state)
        entry = stats.setdefault(user, {"completed": 0, "failed": 0})
        if token == "COMPLETED":
            entry["completed"] += 1
        elif token in _TERMINAL:
            entry["failed"] += 1
    return stats


__all__ = [
    "node_state_counts",
    "partition_utilization",
    "fairshare_scores",
    "recent_completions",
    "job_history",
]
