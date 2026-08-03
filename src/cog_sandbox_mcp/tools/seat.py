"""Seat provisioning tools: mechanize the sandboxed-CC-seat pattern.

Provisions an isolated, co-drivable Claude Code "seat" — its own HOME tree,
its own login keychain, a marketplace + plugin install, and a detached tmux
session running `claude` under that HOME — without ever touching the real
default keychain or an existing OAuth token. See docs/BRIDGE_PATTERN.md for
the sibling convention this borrows its registration-gating idiom from, and
this module's docstrings for the auth-boundary contract each tool enforces.

Registered iff COG_SANDBOX_SEATS_ENABLED is truthy at server startup — the
whole family either appears or doesn't, same posture as the cogos_* bridge
tools gated on COG_OS_BASE_URL.

Platform: macOS only. The keychain step shells out to the Security
framework's `security` CLI, which does not exist elsewhere; `seat_create`
refuses on other platforms with a clear error rather than partially
provisioning a seat with no usable keychain. `seat_list` / `seat_status` /
`seat_destroy` do not touch the keychain directly (delete is a plain
`shutil.rmtree` of the seat's HOME) so they are not platform-gated, but they
do shell out to `tmux` and (for plugin versions) `claude`, neither of which
ship in this package's own container image — see the README's seat section
for why seat tools are a host-side capability, not a sandboxed one.

Userspace-prototype note: this is a userspace mechanization of a pattern
proven by hand. Lifecycle authority (which seats exist, who may spawn one,
how they compose with the kernel's own session registry) is expected to
graduate into the CogOS kernel over time; this tool family is the prototype,
not the final home, for that authority.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

# Env-var knobs. Mirrors the COG_SANDBOX_* naming already used by sandbox.py.
ENV_SEATS_ENABLED = "COG_SANDBOX_SEATS_ENABLED"
ENV_SEATS_ROOT = "COG_SANDBOX_SEATS_ROOT"

DEFAULT_MARKETPLACE = "myrgic/plugins"
DEFAULT_PLUGINS: tuple[str, ...] = ("cogos-harness",)
SEAT_META_FILENAME = ".cog-seat-meta.json"

# Isolation ladder. Only "config" (HOME-tree + keychain isolation) exists
# today; "profile" and "vm" are reserved names for stronger future tiers so
# the interface is forward-stable — a caller asking for "vm" gets a clear
# rejection today, not a silent downgrade to "config" tomorrow.
_ISOLATION_LADDER: tuple[str, ...] = ("config", "profile", "vm")

_SEAT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


# ---------- env / platform ----------


def is_seats_enabled(env: dict[str, str] | None = None) -> bool:
    """Seat tools are registered iff COG_SANDBOX_SEATS_ENABLED is truthy."""
    src = env if env is not None else os.environ
    raw = (src.get(ENV_SEATS_ENABLED) or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def _seats_root() -> Path:
    """Resolve (and create) the parent directory of all provisioned seat HOMEs.

    COG_SANDBOX_SEATS_ROOT, if set, is used verbatim. Otherwise defaults to a
    directory named 'cog-sandbox-seats' alongside COG_SANDBOX_ROOT (i.e. a
    sibling of the fs sandbox root, not inside it — seats are a host-side
    concern, distinct from the sandboxed workspace tree).
    """
    raw = os.environ.get(ENV_SEATS_ROOT, "").strip()
    if raw:
        root = Path(raw)
    else:
        sandbox_root = Path(os.environ.get("COG_SANDBOX_ROOT", "/workspace"))
        root = sandbox_root.parent / "cog-sandbox-seats"
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def _current_platform() -> str:
    """Indirection seam so tests can simulate other platforms without
    mutating the real sys.platform."""
    return sys.platform


def _require_macos() -> None:
    plat = _current_platform()
    if plat != "darwin":
        raise RuntimeError(
            f"seat_create requires macOS: the keychain-isolation step shells "
            f"out to the Security framework's `security` CLI, which only "
            f"exists there. Refusing on platform {plat!r} rather than "
            f"provisioning a seat with no usable keychain."
        )


def _validate_isolation(isolation: str) -> None:
    if isolation not in _ISOLATION_LADDER:
        raise ValueError(
            f"isolation must be one of {list(_ISOLATION_LADDER)}, got {isolation!r}"
        )
    if isolation != "config":
        raise ValueError(
            f"isolation={isolation!r} is reserved but not yet implemented; "
            f"only 'config' is supported today (ladder: "
            f"{'|'.join(_ISOLATION_LADDER)})"
        )


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- seat name / path resolution (traversal guard) ----------


def _normalize_seat_name(name: str) -> str:
    """Validate a seat name used as a tmux session name, HOME directory name,
    and (indirectly) keychain identity.

    Deliberately stricter than sandbox._normalize_workspace_name: seat names
    flow into tmux -s and shell-adjacent contexts, so beyond rejecting path
    separators and '..' we also restrict to a safe charset.
    """
    s = name.strip()
    if not s or s in (".", ".."):
        raise ValueError(f"invalid seat name: {name!r}")
    if "/" in s or "\\" in s:
        raise ValueError(
            f"seat name must be a single path component, not a path: {name!r}"
        )
    if not _SEAT_NAME_RE.match(s):
        raise ValueError(
            f"seat name must match ^[A-Za-z0-9][A-Za-z0-9_-]*$ (it is used "
            f"verbatim as a tmux session name and a HOME directory name); "
            f"got {name!r}"
        )
    return s


def _resolve_seat_home(name: str) -> tuple[str, Path]:
    """Normalize + resolve a seat name to (clean_name, real_home_path).

    Traversal guard: the resolved path must be a direct child of the seats
    root. Existence is NOT checked here — callers decide whether the seat is
    expected to already exist (status/destroy) or must not yet exist (create).
    """
    clean = _normalize_seat_name(name)
    root = _seats_root()
    target = (root / clean).resolve()
    if target.parent != root:
        raise ValueError(f"seat name {name!r} does not resolve under the seats root")
    return clean, target


# ---------- subprocess seam ----------


def _run(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    timeout: float = 30.0,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Thin subprocess.run wrapper — the single seam tests monkeypatch.

    When check=True (default) a non-zero exit raises RuntimeError with the
    command and stderr/stdout attached. Pass check=False for calls (tmux
    has-session, tmux kill-session) where a non-zero exit is an expected,
    meaningful outcome rather than a failure.
    """
    try:
        result = subprocess.run(
            cmd,
            env=env,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            f"required command not found: {cmd[0]!r} (seat tools need tmux, "
            f"claude, and security available on PATH — they are host-side "
            f"tools, not part of this package's own sandbox container image)"
        ) from e
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            f"{' '.join(cmd)} failed (exit {result.returncode}): {detail}"
        )
    return result


# ---------- keychain ----------


def _provision_keychain(home: Path) -> None:
    """Create and unlock a fresh, HOME-scoped login keychain.

    All four `security` calls run with HOME overridden to the seat's HOME, so
    the Security framework resolves ~/Library/Keychains to the seat's tree,
    never the real default keychain. The empty unlock password ("") is a
    local keychain-unlock convenience for a brand-new, empty keychain — it is
    not credential material. This function never reads, writes, or copies any
    OAuth token, API key, or existing credential store; it only creates an
    empty container for a fresh `/login` to persist into.
    """
    env = {**os.environ, "HOME": str(home)}
    _run(["security", "create-keychain", "-p", "", "login.keychain"], env=env)
    _run(["security", "default-keychain", "-s", "login.keychain"], env=env)
    _run(["security", "unlock-keychain", "-p", "", "login.keychain"], env=env)
    _run(["security", "set-keychain-settings", "login.keychain"], env=env)


# ---------- marketplace / plugins ----------


def _marketplace_add(home: Path, marketplace: str) -> str:
    env = {**os.environ, "HOME": str(home)}
    result = _run(
        ["claude", "plugin", "marketplace", "add", marketplace],
        env=env,
        timeout=60.0,
    )
    return result.stdout.strip()


def _plugin_install(home: Path, plugin: str) -> str:
    env = {**os.environ, "HOME": str(home)}
    result = _run(["claude", "plugin", "install", plugin], env=env, timeout=60.0)
    return result.stdout.strip()


def _query_plugin_versions(home: Path) -> Any:
    """Best-effort `claude plugin list --json` under the seat's HOME.

    Non-fatal by design: seat_list must not blow up because one seat hasn't
    logged in yet (claude plugin list may require auth) or `claude` itself is
    unreachable. Returns the parsed JSON on success, or {"error": ...}.
    """
    env = {**os.environ, "HOME": str(home)}
    try:
        result = _run(
            ["claude", "plugin", "list", "--json"], env=env, timeout=15.0, check=True
        )
    except (RuntimeError, subprocess.TimeoutExpired) as e:
        return {"error": f"{type(e).__name__}: {e}"}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "claude plugin list --json returned non-JSON output"}


# ---------- tmux ----------


def _tmux_new_session(name: str, work_dir: Path, home: Path) -> None:
    _run(
        [
            "tmux",
            "new-session",
            "-d",
            "-s",
            name,
            "-c",
            str(work_dir),
            "-e",
            f"HOME={home}",
            "claude; zsh",
        ]
    )


def _tmux_target_session(name: str) -> str:
    """tmux target-session string pinned to an EXACT match.

    Without the leading '=', tmux resolves a target by exact match, then by
    PREFIX, then by fnmatch pattern. That fallback is a cross-session hazard
    here: a seat named 'cogos' whose own tmux session has already exited would
    otherwise resolve to an unrelated live session like 'cogos-dogfood' —
    making `seat_destroy` kill the operator's session and `seat_status` dump
    its pane. The '=' prefix disables prefix/fnmatch fallback entirely.
    """
    return f"={name}"


def _tmux_target_pane(name: str) -> str:
    """Exact-match target-pane for the seat's session (trailing ':' selects
    that session's current window/pane)."""
    return f"={name}:"


def _tmux_has_session(name: str) -> bool:
    result = _run(
        ["tmux", "has-session", "-t", _tmux_target_session(name)], check=False
    )
    return result.returncode == 0


def _tmux_kill_session(name: str) -> bool:
    result = _run(
        ["tmux", "kill-session", "-t", _tmux_target_session(name)], check=False
    )
    return result.returncode == 0


def _tmux_capture_pane(name: str, lines: int) -> str:
    result = _run(
        [
            "tmux",
            "capture-pane",
            "-t",
            _tmux_target_pane(name),
            "-p",
            "-S",
            f"-{lines}",
        ],
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout


# ---------- CogOS bridge registry lookups ----------


def _registry_sessions_for_seat(work_dir: Path) -> dict[str, Any]:
    """Sessions the kernel currently tracks whose workspace is this seat's
    work dir. Only runs when COG_OS_BASE_URL is set — same gate as the
    cogos_* bridge tools; when unset, returns {"enabled": False}."""
    from cog_sandbox_mcp.tools import cogos_bridge

    if not cogos_bridge.is_bridge_enabled():
        return {"enabled": False, "sessions": []}
    body = cogos_bridge.cogos_sessions_list(active_within_seconds=86400)
    if isinstance(body, dict) and body.get("success") is False:
        return {"enabled": True, "error": body.get("error"), "sessions": []}
    rows = body.get("sessions") if isinstance(body, dict) else None
    if not isinstance(rows, list):
        return {
            "enabled": True,
            "error": "unexpected registry response shape",
            "sessions": [],
        }
    matched = [
        r for r in rows if isinstance(r, dict) and r.get("workspace") == str(work_dir)
    ]
    return {"enabled": True, "sessions": matched}


# ---------- tools ----------


def seat_create(
    name: str,
    marketplace: str = DEFAULT_MARKETPLACE,
    plugins: list[str] | None = None,
    isolation: str = "config",
) -> dict[str, Any]:
    """Provision an isolated, co-drivable Claude Code seat.

    Mechanizes the sandboxed-CC-seat pattern: an isolated HOME tree, an
    isolated login keychain, a marketplace + plugin install, and a detached
    tmux session running `claude` — all HOME-scoped so nothing here touches
    the operator's live seat, its plugin state, or its tokens.

    CALL THIS WHEN you need a Claude Code instance that both the operator and
    this session can co-drive over tmux, isolated from the live seat — e.g.
    testing a plugin or marketplace change end-to-end, or standing up a
    dedicated worker seat. Do NOT use this to duplicate or extend the
    operator's own session; each seat mints its own independent OAuth grant.

    Isolation ladder: only "config" (HOME-tree + keychain isolation) is
    implemented. "profile" and "vm" are reserved names for stronger future
    tiers and are rejected with a ValueError naming the full ladder, so a
    caller asking for one never silently gets "config" instead.

    Steps performed:
      1. Create `<seats_root>/<name>` (the seat's HOME) and `<home>/work`
         (the tmux session's cwd).
      2. Create and unlock a fresh, HOME-scoped login keychain.
      3. `claude plugin marketplace add <marketplace>`, then `claude plugin
         install <plugin>` for each of `plugins` (default: `myrgic/plugins` +
         `cogos-harness`), both HOME-scoped.
      4. Spawn a detached tmux session running `claude` under that HOME.
      A failure at any provisioning step rolls back (deletes the partially
      built HOME) before the exception propagates — a failed provision never
      leaves a half-built seat directory that looks live.

    Auth boundary — read this before attaching: this tool never touches
    credential material. It creates an EMPTY keychain so a fresh `/login` has
    somewhere to persist a token; it does not read, copy, or graft any
    existing OAuth token, API key, or `.credentials.json` from the operator's
    seat or anywhere else. The operator (or a co-driving root seat) MUST run
    `/login` inside the attached tmux pane — this mints the seat's own,
    independently-rotating OAuth grant. Watch the auth banner after login: it
    may default to a metered Console/org account rather than the intended
    Max-plan subscription account — pick the right account during `/login`.

    Platform: macOS only. Raises RuntimeError naming the current platform on
    any other OS, before touching disk, rather than partially provisioning a
    seat with no usable keychain.

    Arguments:
      name:        seat identifier. Used verbatim as the tmux session name
                   and the HOME directory name under the seats root. Must
                   match `^[A-Za-z0-9][A-Za-z0-9_-]*$`.
      marketplace: plugin marketplace to add (default "myrgic/plugins").
      plugins:     plugin names to install after the marketplace add
                   (default `["cogos-harness"]`). Pass `[]` to add the
                   marketplace but skip plugin install.
      isolation:   isolation tier. Only "config" is implemented today.

    Returns: `{"name", "home", "work_dir", "tmux_session",
    "tmux_attach_command", "marketplace", "plugins", "isolation",
    "login_required": True, "note"}`. Raises `FileExistsError` if a seat with
    this name is already provisioned, `ValueError` for a bad name or
    unsupported isolation tier, `RuntimeError` on a non-macOS platform or if
    any provisioning subprocess step fails.
    """
    _validate_isolation(isolation)
    _require_macos()
    clean_name, home = _resolve_seat_home(name)
    if home.exists():
        raise FileExistsError(f"seat {clean_name!r} already exists at {home}")

    plugin_list = list(plugins) if plugins is not None else list(DEFAULT_PLUGINS)

    work_dir = home / "work"
    home.mkdir(parents=True)
    work_dir.mkdir()

    try:
        _provision_keychain(home)
        _marketplace_add(home, marketplace)
        for plugin in plugin_list:
            _plugin_install(home, plugin)
        _tmux_new_session(clean_name, work_dir, home)
    except Exception:
        # Best-effort rollback: a failed provision should not leave a
        # half-built seat directory sitting under the seats root looking live.
        shutil.rmtree(home, ignore_errors=True)
        raise

    meta = {
        "name": clean_name,
        "created_at": _utc_now_iso(),
        "marketplace": marketplace,
        "plugins": plugin_list,
        "isolation": isolation,
    }
    (home / SEAT_META_FILENAME).write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return {
        "name": clean_name,
        "home": str(home),
        "work_dir": str(work_dir),
        "tmux_session": clean_name,
        "tmux_attach_command": f"tmux attach -t {clean_name}",
        "marketplace": marketplace,
        "plugins": plugin_list,
        "isolation": isolation,
        "login_required": True,
        "note": (
            "Attach to the tmux session and run /login inside it. This mints "
            "a FRESH OAuth grant scoped to this seat — never copy or share "
            "credentials from another seat or the operator's own session. "
            "Check the auth banner after login: pick the Max-plan "
            "subscription account, not a metered Console/org account, if "
            "prompted."
        ),
    }


def seat_list() -> dict[str, Any]:
    """List provisioned seats with tmux-alive status and installed plugin versions.

    CALL THIS WHEN you need an inventory of currently-provisioned seats before
    attaching, destroying, or provisioning a new one under the same name.

    Scans direct children of the seats root that carry a seat metadata file
    (`.cog-seat-meta.json`, written by `seat_create`); bare directories
    without it are not seats and are skipped. `alive` reflects `tmux
    has-session`, not whether the seat has completed `/login` — a
    provisioned-but-not-logged-in seat still shows `alive: True` once its
    tmux session is up. `plugins` reflects a live `claude plugin list --json`
    query under the seat's HOME; on query failure (e.g. `claude` unreachable,
    seat not yet logged in) it is replaced with `{"error": ...}` rather than
    raising the whole tool.

    Returns: `{"seats": [{"name", "home", "alive", "marketplace", "plugins",
    "isolation", "created_at"}], "count": N}`.
    """
    root = _seats_root()
    seats: list[dict[str, Any]] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        meta_path = entry / SEAT_META_FILENAME
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            meta = {}
        name = meta.get("name", entry.name)
        seats.append(
            {
                "name": name,
                "home": str(entry),
                "alive": _tmux_has_session(name),
                "marketplace": meta.get("marketplace"),
                "plugins": _query_plugin_versions(entry),
                "isolation": meta.get("isolation"),
                "created_at": meta.get("created_at"),
            }
        )
    return {"seats": seats, "count": len(seats)}


def seat_status(name: str, lines: int = 100) -> dict[str, Any]:
    """Report a seat's live pane tail and its kernel registry footprint.

    CALL THIS WHEN checking whether a seat is still alive, what it's
    currently doing (pane tail), or whether it has any sessions registered on
    the CogOS kernel (e.g. after the operator has logged in and the seat's
    own Claude Code session has called `cogos_session_register`).

    Registry check only runs when `COG_OS_BASE_URL` is set at server startup
    (same gate as the `cogos_*` bridge tools); when unset, `registry.enabled`
    is `False` and `registry.sessions` is empty rather than raising. Matching
    is by exact `workspace` equality against the seat's work directory — only
    sessions registered with `workspace=<seat's work_dir>` are attributed to
    this seat.

    Arguments:
      name:  the seat's name, as passed to `seat_create`.
      lines: how many lines of tmux scrollback to capture (default 100).

    Returns: `{"name", "alive", "tmux_session", "pane_tail", "registry":
    {"enabled", "sessions", "error"?}}`. Raises `FileNotFoundError` if no
    seat with this name is provisioned, `ValueError` if the name fails the
    traversal guard.
    """
    clean_name, home = _resolve_seat_home(name)
    if not home.exists():
        raise FileNotFoundError(f"seat {clean_name!r} not found under seats root")
    work_dir = home / "work"
    alive = _tmux_has_session(clean_name)
    pane_tail = _tmux_capture_pane(clean_name, lines) if alive else ""
    registry = _registry_sessions_for_seat(work_dir)
    return {
        "name": clean_name,
        "alive": alive,
        "tmux_session": clean_name,
        "pane_tail": pane_tail,
        "registry": registry,
    }


def seat_destroy(name: str) -> dict[str, Any]:
    """Tear down a seat: kill its tmux session, end its kernel registry rows,
    and delete its HOME (including its isolated keychain).

    CALL THIS WHEN a seat's work is done and it should stop consuming a tmux
    session and disk. Irreversible — the seat's HOME (work dir, keychain,
    plugin state, and any files the seat wrote) is permanently deleted.

    Traversal guard: refuses (`ValueError`) if `name` does not resolve to a
    direct child of the seats root — enforced before anything is touched,
    since this is a delete operation.

    Steps:
      1. `tmux kill-session -t <name>` (non-fatal if already dead).
      2. If `COG_OS_BASE_URL` is set: look up any kernel-registered sessions
         whose `workspace` matches this seat's work dir and end each one via
         `cogos_session_end(session_id, reason="session_end_hook")`.
      3. `shutil.rmtree` the seat's HOME. This removes the keychain file
         along with everything else under HOME — there is no separate
         keychain-delete step because the keychain is entirely HOME-scoped.

    Arguments:
      name: the seat's name, as passed to `seat_create`.

    Returns: `{"name", "tmux_killed", "registry_sessions_ended",
    "home_removed"}`. Raises `FileNotFoundError` if no seat with this name is
    provisioned, `ValueError` if the name fails the traversal guard.
    """
    clean_name, home = _resolve_seat_home(name)
    if not home.exists():
        raise FileNotFoundError(f"seat {clean_name!r} not found under seats root")
    work_dir = home / "work"

    tmux_killed = _tmux_kill_session(clean_name)

    ended: list[str] = []
    registry = _registry_sessions_for_seat(work_dir)
    if registry.get("enabled"):
        from cog_sandbox_mcp.tools import cogos_bridge

        for row in registry.get("sessions", []):
            session_id = row.get("session_id") if isinstance(row, dict) else None
            if not session_id:
                continue
            result = cogos_bridge.cogos_session_end(
                session_id, reason="session_end_hook"
            )
            if not (isinstance(result, dict) and result.get("success") is False):
                ended.append(session_id)

    shutil.rmtree(home)

    return {
        "name": clean_name,
        "tmux_killed": tmux_killed,
        "registry_sessions_ended": ended,
        "home_removed": True,
    }


def register(mcp: FastMCP) -> None:
    """Register seat tools with the MCP server.

    Gated on COG_SANDBOX_SEATS_ENABLED — mirrors the cogos_bridge
    conditional-registration pattern (docs/BRIDGE_PATTERN.md §
    Registration): the whole family either appears or doesn't, no per-tool
    gating. Caller must not rely on per-tool checks inside each function.
    """
    if not is_seats_enabled():
        return
    mcp.tool(
        title="Create seat",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=True,
        ),
    )(seat_create)
    mcp.tool(
        title="List seats",
        annotations=ToolAnnotations(
            readOnlyHint=True, idempotentHint=True, openWorldHint=True
        ),
    )(seat_list)
    mcp.tool(
        title="Seat status",
        annotations=ToolAnnotations(
            readOnlyHint=True, idempotentHint=True, openWorldHint=True
        ),
    )(seat_status)
    mcp.tool(
        title="Destroy seat",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=True,
        ),
    )(seat_destroy)
