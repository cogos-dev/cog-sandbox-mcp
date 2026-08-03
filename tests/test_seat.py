"""Tests for the seat_* provisioning tool family (src/cog_sandbox_mcp/tools/seat.py).

All subprocess calls (security, claude, tmux) are mocked via seat._run —
no live `claude` binary, tmux, or macOS keychain is required. Platform is
simulated via seat._current_platform() rather than mutating sys.platform.
"""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from cog_sandbox_mcp.tools import seat


# ---------- fixtures ----------


@pytest.fixture
def seats_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "seats"
    monkeypatch.setenv(seat.ENV_SEATS_ENABLED, "1")
    monkeypatch.setenv(seat.ENV_SEATS_ROOT, str(root))
    return root


@pytest.fixture
def macos(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(seat, "_current_platform", lambda: "darwin")


def _fake_run_ok(cmd: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")


@pytest.fixture
def recording_run(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Replace seat._run with a recorder that always succeeds; returns the
    list of recorded argv lists in call order."""
    calls: list[list[str]] = []

    def fake(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(seat, "_run", fake)
    return calls


# ---------- env / gating ----------


def test_seats_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(seat.ENV_SEATS_ENABLED, raising=False)
    assert seat.is_seats_enabled() is False


def test_seats_enabled_truthy_values(monkeypatch: pytest.MonkeyPatch) -> None:
    for val in ("1", "true", "True", "yes", "on"):
        monkeypatch.setenv(seat.ENV_SEATS_ENABLED, val)
        assert seat.is_seats_enabled() is True
    monkeypatch.setenv(seat.ENV_SEATS_ENABLED, "0")
    assert seat.is_seats_enabled() is False


def test_seat_tools_not_registered_when_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    monkeypatch.setenv("COG_SANDBOX_ROOT", str(tmp_path))
    monkeypatch.setenv("COG_SANDBOX_INITIAL_AUTH", "ws")
    monkeypatch.delenv(seat.ENV_SEATS_ENABLED, raising=False)
    from cog_sandbox_mcp import sandbox

    sandbox.initialize_auth()
    from cog_sandbox_mcp.server import build_server
    import asyncio

    tools = asyncio.run(build_server().list_tools())
    names = [t.name for t in tools]
    assert "seat_create" not in names
    assert "seat_list" not in names
    assert "seat_status" not in names
    assert "seat_destroy" not in names


def test_seat_tools_registered_when_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    monkeypatch.setenv("COG_SANDBOX_ROOT", str(tmp_path))
    monkeypatch.setenv("COG_SANDBOX_INITIAL_AUTH", "ws")
    monkeypatch.setenv(seat.ENV_SEATS_ENABLED, "1")
    monkeypatch.setenv(seat.ENV_SEATS_ROOT, str(tmp_path / "seats"))
    from cog_sandbox_mcp import sandbox

    sandbox.initialize_auth()
    from cog_sandbox_mcp.server import build_server
    import asyncio

    tools = asyncio.run(build_server().list_tools())
    names = [t.name for t in tools]
    assert {"seat_create", "seat_list", "seat_status", "seat_destroy"} <= set(names)


# ---------- name validation / traversal guard ----------


@pytest.mark.parametrize("bad", ["", ".", "..", "a/b", "a\\b", "../escape", "-lead"])
def test_normalize_seat_name_rejects_bad_names(bad: str) -> None:
    with pytest.raises(ValueError):
        seat._normalize_seat_name(bad)


def test_normalize_seat_name_accepts_good_names() -> None:
    assert seat._normalize_seat_name(" alpha-1_ok ") == "alpha-1_ok"


def test_resolve_seat_home_traversal_guard(seats_root: Path) -> None:
    # "../outside" is already rejected by _normalize_seat_name (no path
    # separators allowed) — that IS the traversal guard's first layer.
    with pytest.raises(ValueError, match="single path component"):
        seat._resolve_seat_home("../outside")


def test_resolve_seat_home_parent_check_is_defense_in_depth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Even if a name somehow passed normalization, _resolve_seat_home
    # independently verifies the resolved path's parent equals the seats
    # root before returning it — belt-and-suspenders against a future
    # relaxation of the name charset that might otherwise let a crafted
    # name (e.g. one that resolves via a symlink) escape.
    fake_root = Path("/tmp/fake-seats-root")
    monkeypatch.setattr(seat, "_normalize_seat_name", lambda name: "sneaky")
    monkeypatch.setattr(seat, "_seats_root", lambda: fake_root)
    monkeypatch.setattr(
        Path,
        "resolve",
        lambda self: (
            Path("/tmp/somewhere-else/sneaky") if self == fake_root / "sneaky" else self
        ),
    )
    with pytest.raises(ValueError, match="does not resolve under the seats root"):
        seat._resolve_seat_home("anything")


def test_seat_status_traversal_guard_before_touching_disk(seats_root: Path) -> None:
    with pytest.raises(ValueError):
        seat.seat_status("../etc")
    # Nothing should have been created as a side effect of a rejected name.
    assert not seats_root.exists() or list(seats_root.iterdir()) == []


def test_seat_destroy_traversal_guard_before_touching_disk(seats_root: Path) -> None:
    with pytest.raises(ValueError):
        seat.seat_destroy("../etc")
    assert not seats_root.exists() or list(seats_root.iterdir()) == []


# ---------- seat_create ----------


def test_seat_create_rejects_non_macos(
    seats_root: Path, monkeypatch: pytest.MonkeyPatch, recording_run: list[list[str]]
) -> None:
    monkeypatch.setattr(seat, "_current_platform", lambda: "linux")
    with pytest.raises(RuntimeError, match="macOS"):
        seat.seat_create("alpha")
    assert recording_run == []  # bails before any subprocess call
    assert not (seats_root / "alpha").exists()


def test_seat_create_rejects_unsupported_isolation(
    seats_root: Path, macos: None, recording_run: list[list[str]]
) -> None:
    with pytest.raises(ValueError, match=r"config\|profile\|vm"):
        seat.seat_create("alpha", isolation="vm")
    assert recording_run == []


def test_seat_create_rejects_unknown_isolation_value(
    seats_root: Path, macos: None
) -> None:
    with pytest.raises(ValueError, match="isolation must be one of"):
        seat.seat_create("alpha", isolation="bogus")


def test_seat_create_provisioning_layout(
    seats_root: Path, macos: None, recording_run: list[list[str]]
) -> None:
    result = seat.seat_create("alpha")

    home = seats_root / "alpha"
    work = home / "work"
    assert home.is_dir()
    assert work.is_dir()

    meta = json.loads((home / seat.SEAT_META_FILENAME).read_text())
    assert meta["name"] == "alpha"
    assert meta["marketplace"] == seat.DEFAULT_MARKETPLACE
    assert meta["plugins"] == list(seat.DEFAULT_PLUGINS)
    assert meta["isolation"] == "config"

    assert result["name"] == "alpha"
    assert result["home"] == str(home)
    assert result["work_dir"] == str(work)
    assert result["tmux_session"] == "alpha"
    assert result["tmux_attach_command"] == "tmux attach -t alpha"
    assert result["login_required"] is True
    assert "/login" in result["note"]
    assert "never" in result["note"].lower()

    # Keychain create/unlock, marketplace add, plugin install, tmux spawn —
    # in that order.
    joined = [" ".join(c) for c in recording_run]
    assert any(c[:2] == ["security", "create-keychain"] for c in recording_run)
    assert any(c[:2] == ["security", "default-keychain"] for c in recording_run)
    assert any(c[:2] == ["security", "unlock-keychain"] for c in recording_run)
    assert any(c[:2] == ["security", "set-keychain-settings"] for c in recording_run)
    assert any(
        c[:4] == ["claude", "plugin", "marketplace", "add"] for c in recording_run
    )
    assert any(c[:3] == ["claude", "plugin", "install"] for c in recording_run)
    tmux_calls = [c for c in recording_run if c[0] == "tmux"]
    assert len(tmux_calls) == 1
    tmux_cmd = tmux_calls[0]
    assert tmux_cmd[:4] == ["tmux", "new-session", "-d", "-s"]
    assert "alpha" in tmux_cmd
    assert f"HOME={home}" in tmux_cmd
    assert joined  # sanity: something was recorded


def test_seat_create_custom_marketplace_and_plugins(
    seats_root: Path, macos: None, recording_run: list[list[str]]
) -> None:
    result = seat.seat_create(
        "beta", marketplace="acme/plugins", plugins=["one", "two"]
    )
    assert result["marketplace"] == "acme/plugins"
    assert result["plugins"] == ["one", "two"]
    install_calls = [
        c for c in recording_run if c[:3] == ["claude", "plugin", "install"]
    ]
    assert [c[3] for c in install_calls] == ["one", "two"]


def test_seat_create_empty_plugins_skips_install(
    seats_root: Path, macos: None, recording_run: list[list[str]]
) -> None:
    seat.seat_create("gamma", plugins=[])
    install_calls = [
        c for c in recording_run if c[:3] == ["claude", "plugin", "install"]
    ]
    assert install_calls == []
    # Marketplace add still happens.
    assert any(
        c[:4] == ["claude", "plugin", "marketplace", "add"] for c in recording_run
    )


def test_seat_create_refuses_duplicate(
    seats_root: Path, macos: None, recording_run: list[list[str]]
) -> None:
    seat.seat_create("alpha")
    with pytest.raises(FileExistsError):
        seat.seat_create("alpha")


def test_seat_create_rolls_back_on_failure(
    seats_root: Path, macos: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def flaky(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        if cmd[0] == "tmux":
            raise RuntimeError("tmux exploded")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(seat, "_run", flaky)
    with pytest.raises(RuntimeError, match="tmux exploded"):
        seat.seat_create("alpha")
    assert not (seats_root / "alpha").exists()


# ---------- seat_list ----------


def _write_seat_dir(
    root: Path, name: str, *, marketplace: str = "myrgic/plugins"
) -> Path:
    home = root / name
    (home / "work").mkdir(parents=True)
    meta = {
        "name": name,
        "created_at": "2026-08-03T00:00:00+00:00",
        "marketplace": marketplace,
        "plugins": ["cogos-harness"],
        "isolation": "config",
    }
    (home / seat.SEAT_META_FILENAME).write_text(json.dumps(meta))
    return home


def test_seat_list_empty_root(seats_root: Path) -> None:
    assert seat.seat_list() == {"seats": [], "count": 0}


def test_seat_list_skips_non_seat_dirs(
    seats_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_seat_dir(seats_root, "alpha")
    stray = seats_root / "not-a-seat"
    stray.mkdir(parents=True)
    (stray / "somefile.txt").write_text("hi")

    monkeypatch.setattr(seat, "_tmux_has_session", lambda name: True)
    monkeypatch.setattr(seat, "_query_plugin_versions", lambda home: [])

    result = seat.seat_list()
    names = [s["name"] for s in result["seats"]]
    assert names == ["alpha"]
    assert result["count"] == 1


def test_seat_list_reports_alive_and_plugins(
    seats_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_seat_dir(seats_root, "alpha")
    _write_seat_dir(seats_root, "beta")

    def fake_alive(name: str) -> bool:
        return name == "alpha"

    def fake_versions(home: Path) -> Any:
        return [{"name": "cogos-harness", "version": "0.1.0"}]

    monkeypatch.setattr(seat, "_tmux_has_session", fake_alive)
    monkeypatch.setattr(seat, "_query_plugin_versions", fake_versions)

    result = seat.seat_list()
    by_name = {s["name"]: s for s in result["seats"]}
    assert result["count"] == 2
    assert by_name["alpha"]["alive"] is True
    assert by_name["beta"]["alive"] is False
    assert by_name["alpha"]["plugins"] == [
        {"name": "cogos-harness", "version": "0.1.0"}
    ]
    assert by_name["alpha"]["marketplace"] == "myrgic/plugins"
    assert by_name["alpha"]["isolation"] == "config"


# ---------- seat_status ----------


def test_seat_status_not_found(seats_root: Path) -> None:
    with pytest.raises(FileNotFoundError):
        seat.seat_status("nope")


def test_seat_status_dead_seat_no_pane_tail(
    seats_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_seat_dir(seats_root, "alpha")
    monkeypatch.setattr(seat, "_tmux_has_session", lambda name: False)

    def boom(name: str, lines: int) -> str:
        raise AssertionError("capture-pane should not be called for a dead session")

    monkeypatch.setattr(seat, "_tmux_capture_pane", boom)
    monkeypatch.delenv("COG_OS_BASE_URL", raising=False)

    result = seat.seat_status("alpha")
    assert result["alive"] is False
    assert result["pane_tail"] == ""
    assert result["registry"] == {"enabled": False, "sessions": []}


def test_seat_status_alive_captures_pane_and_registry_disabled(
    seats_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_seat_dir(seats_root, "alpha")
    monkeypatch.setattr(seat, "_tmux_has_session", lambda name: True)
    monkeypatch.setattr(
        seat, "_tmux_capture_pane", lambda name, lines: "hello from pane\n"
    )
    monkeypatch.delenv("COG_OS_BASE_URL", raising=False)

    result = seat.seat_status("alpha", lines=50)
    assert result["alive"] is True
    assert result["pane_tail"] == "hello from pane\n"
    assert result["registry"]["enabled"] is False


def test_seat_status_registry_enabled_matches_by_workspace(
    seats_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = _write_seat_dir(seats_root, "alpha")
    work_dir = home / "work"
    monkeypatch.setattr(seat, "_tmux_has_session", lambda name: True)
    monkeypatch.setattr(seat, "_tmux_capture_pane", lambda name, lines: "")
    monkeypatch.setenv("COG_OS_BASE_URL", "http://127.0.0.1:5100")

    from cog_sandbox_mcp.tools import cogos_bridge

    def fake_sessions_list(
        active_within_seconds: int = 600, include_ended: bool = False
    ) -> dict[str, Any]:
        return {
            "sessions": [
                {"session_id": "s-1", "workspace": str(work_dir)},
                {"session_id": "s-2", "workspace": "/somewhere/else"},
            ],
            "count": 2,
        }

    monkeypatch.setattr(cogos_bridge, "cogos_sessions_list", fake_sessions_list)

    result = seat.seat_status("alpha")
    assert result["registry"]["enabled"] is True
    ids = [r["session_id"] for r in result["registry"]["sessions"]]
    assert ids == ["s-1"]


# ---------- seat_destroy ----------


def test_seat_destroy_not_found(seats_root: Path) -> None:
    with pytest.raises(FileNotFoundError):
        seat.seat_destroy("nope")


def test_seat_destroy_cleanup(
    seats_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = _write_seat_dir(seats_root, "alpha")
    (home / "Library" / "Keychains").mkdir(parents=True)
    (home / "Library" / "Keychains" / "login.keychain-db").write_text("x")

    monkeypatch.setattr(seat, "_tmux_kill_session", lambda name: True)
    monkeypatch.delenv("COG_OS_BASE_URL", raising=False)

    result = seat.seat_destroy("alpha")

    assert result["name"] == "alpha"
    assert result["tmux_killed"] is True
    assert result["registry_sessions_ended"] == []
    assert result["home_removed"] is True
    assert not home.exists()


def test_seat_destroy_ends_matching_registry_sessions(
    seats_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = _write_seat_dir(seats_root, "alpha")
    work_dir = home / "work"
    monkeypatch.setattr(seat, "_tmux_kill_session", lambda name: True)
    monkeypatch.setenv("COG_OS_BASE_URL", "http://127.0.0.1:5100")

    from cog_sandbox_mcp.tools import cogos_bridge

    def fake_sessions_list(
        active_within_seconds: int = 600, include_ended: bool = False
    ) -> dict[str, Any]:
        return {
            "sessions": [
                {"session_id": "s-1", "workspace": str(work_dir)},
                {"session_id": "s-2", "workspace": "/somewhere/else"},
            ],
            "count": 2,
        }

    ended_calls: list[dict[str, Any]] = []

    def fake_end(
        session_id: str, reason: str = "user-quit", handoff_id: str | None = None
    ) -> dict[str, Any]:
        ended_calls.append({"session_id": session_id, "reason": reason})
        return {"ok": True}

    monkeypatch.setattr(cogos_bridge, "cogos_sessions_list", fake_sessions_list)
    monkeypatch.setattr(cogos_bridge, "cogos_session_end", fake_end)

    result = seat.seat_destroy("alpha")

    assert result["registry_sessions_ended"] == ["s-1"]
    assert ended_calls == [{"session_id": "s-1", "reason": "session_end_hook"}]
    assert not home.exists()


def test_seat_destroy_does_not_end_session_when_kernel_reports_failure(
    seats_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = _write_seat_dir(seats_root, "alpha")
    work_dir = home / "work"
    monkeypatch.setattr(seat, "_tmux_kill_session", lambda name: False)
    monkeypatch.setenv("COG_OS_BASE_URL", "http://127.0.0.1:5100")

    from cog_sandbox_mcp.tools import cogos_bridge

    def fake_sessions_list(
        active_within_seconds: int = 600, include_ended: bool = False
    ) -> dict[str, Any]:
        return {
            "sessions": [{"session_id": "s-1", "workspace": str(work_dir)}],
            "count": 1,
        }

    def fake_end(
        session_id: str, reason: str = "user-quit", handoff_id: str | None = None
    ) -> dict[str, Any]:
        return {"success": False, "error": "kernel unreachable"}

    monkeypatch.setattr(cogos_bridge, "cogos_sessions_list", fake_sessions_list)
    monkeypatch.setattr(cogos_bridge, "cogos_session_end", fake_end)

    result = seat.seat_destroy("alpha")
    assert result["tmux_killed"] is False
    assert result["registry_sessions_ended"] == []
    # Home is still removed even though the registry end failed — cleanup is
    # not gated on the kernel being reachable.
    assert result["home_removed"] is True
    assert not home.exists()


# ---------- _run seam ----------


def test_run_missing_binary_raises_clear_runtime_error(
    seats_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(RuntimeError, match="required command not found"):
        seat._run(["definitely-not-a-real-binary-xyz"])


def test_run_check_false_does_not_raise_on_nonzero_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="not found")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = seat._run(["tmux", "has-session", "-t", "nope"], check=False)
    assert result.returncode == 1


# ---------- tmux target exactness (cross-session collateral guard) ----------
#
# Regression: tmux resolves a bare target-session by exact match, then by
# PREFIX, then by fnmatch. A seat whose own tmux session has exited would
# otherwise prefix-match an unrelated live session (e.g. seat "cogos" ->
# "cogos-dogfood"), so seat_destroy would kill the operator's session and
# seat_status would capture its pane. These assert on the real argv, since
# the helper-level mocks used elsewhere cannot catch a bad -t argument.


def _capture_tmux_argv(monkeypatch: pytest.MonkeyPatch, returncode: int = 0) -> list:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    return calls


def test_tmux_has_session_uses_exact_match_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _capture_tmux_argv(monkeypatch)
    seat._tmux_has_session("cogos")
    assert calls[0] == ["tmux", "has-session", "-t", "=cogos"]


def test_tmux_kill_session_uses_exact_match_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _capture_tmux_argv(monkeypatch)
    seat._tmux_kill_session("cogos")
    assert calls[0] == ["tmux", "kill-session", "-t", "=cogos"]
    # The bare name would prefix-match 'cogos-dogfood' and kill it.
    assert "cogos" not in calls[0][3:] or calls[0][3].startswith("=")


def test_tmux_capture_pane_uses_exact_match_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _capture_tmux_argv(monkeypatch)
    seat._tmux_capture_pane("cogos", 50)
    assert calls[0][:4] == ["tmux", "capture-pane", "-t", "=cogos:"]


def test_seat_destroy_targets_only_the_exact_session(
    seats_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end argv check: destroying a seat must not emit a bare target."""
    home = seats_root / "cogos"
    (home / "work").mkdir(parents=True)
    (home / seat.SEAT_META_FILENAME).write_text("{}", encoding="utf-8")

    calls = _capture_tmux_argv(monkeypatch)
    seat.seat_destroy("cogos")

    kill = [c for c in calls if c[:2] == ["tmux", "kill-session"]]
    assert len(kill) == 1
    assert kill[0][-1] == "=cogos"
