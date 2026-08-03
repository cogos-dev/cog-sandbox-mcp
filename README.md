# cog-sandbox-mcp

Cog OS filesystem-coding-agent sandbox exposed via the Model Context Protocol.

Runs an MCP client's filesystem access through a rootless, network-isolated
container, authorized one workspace at a time. Ships two tool families:
structured filesystem tools (`read`, `write`, `edit`, `glob`, `grep`, `tree`,
`list_directory`, plus duplicate-file helpers) that are always available, and
an optional Cog OS bridge (`cogos_*` tools, gated on `COG_OS_BASE_URL`) that
lets a sandboxed session register itself with a kernel, read and write a
kernel-held event bus, and hand a task off to another session. See
[Cog OS bridge tools](#cog-os-bridge-tools) below for the full list.

## Transports

### stdio (default)

Unchanged. Launch via `python -m cog_sandbox_mcp` (or the `cog-sandbox-mcp`
console script). One subprocess per MCP client.

### HTTP (Streamable-HTTP) — opt-in

Run one centralized server and connect multiple Claude Code sessions as
independent clients via `mcp-remote`.

Env-var switches (all optional, stdio remains the default):

| Env var           | Default     | Purpose                                         |
|-------------------|-------------|-------------------------------------------------|
| `MCP_TRANSPORT`   | `stdio`     | `http` / `streamable-http` to enable HTTP mode  |
| `MCP_HTTP_HOST`   | `127.0.0.1` | Bind address                                    |
| `MCP_HTTP_PORT`   | `7823`      | Bind port                                       |
| `MCP_HTTP_PATH`   | `/mcp`      | URL path for the Streamable-HTTP endpoint       |

Launch:

```bash
MCP_TRANSPORT=http python -m cog_sandbox_mcp
# -> INFO  cog-sandbox-mcp HTTP transport listening at http://127.0.0.1:7823/mcp
```

Wire into `.mcp.json` (Claude Code) using `mcp-remote`:

```json
{
  "mcpServers": {
    "cog-sandbox": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://127.0.0.1:7823/mcp"]
    }
  }
}
```

Each session spawns its own `mcp-remote` stdio shim that proxies JSON-RPC to the
shared HTTP server — the server sees each Claude Code session as an independent
client.

## Environment for the sandbox itself

- `COG_SANDBOX_ROOT` — parent directory of per-session workspaces.
- `COG_SANDBOX_INITIAL_AUTH` — colon-separated list of workspace names to
  pre-authorize on startup.
- `COG_OS_BASE_URL` — if set, Cog OS bridge tools are registered. See
  [`docs/BRIDGE_PATTERN.md`](docs/BRIDGE_PATTERN.md).

## Cog OS bridge tools

These tools only appear in the MCP tool list when `COG_OS_BASE_URL` is set at
server startup. They call the kernel's `/v1/*` HTTP surface directly over
plain HTTP, separate from the sandboxed container's own `--network=none`
boundary: bridge calls go out from the MCP server process, not from inside
the sandbox.

| Tool | What it does |
|---|---|
| `cogos_status` | Checks whether the configured kernel is reachable. |
| `cogos_emit` | Emits an event onto a Cog OS bus channel. |
| `cogos_events_read` | Reads events from a bus (read-only; does not create the bus). |
| `cogos_resolve` | Resolves a `cog://` URI and returns its contents. **Currently broken; see below.** |
| `cogos_session_register` | Announces a session's presence on the kernel's session registry. |
| `cogos_session_heartbeat` | Sends a periodic keep-alive for a registered session. |
| `cogos_session_end` | Marks a session as ended. |
| `cogos_sessions_list` | Lists sessions the kernel currently tracks. |
| `cogos_handoff_offer` | Publishes a handoff offer (task + bootstrap prompt) for another session to pick up. |
| `cogos_handoff_list_open` | Lists handoff offers currently available to claim. |
| `cogos_handoff_claim` | Claims an open handoff offer and returns its full payload. |
| `cogos_handoff_complete` | Marks a claimed handoff as finished. |
| `cogos_channel_join` | Joins a channel (voice or text) for a registered session. |
| `cogos_channel_leave` | Leaves a channel. |

The session and handoff tools together implement an identity + handoff
protocol: a session registers, works, and either ends cleanly or offers a
handoff that a successor session claims and completes. See
[`docs/BRIDGE_PATTERN.md`](docs/BRIDGE_PATTERN.md) for the wire conventions
shared across these tools, and `CHANGELOG.md` for the version each tool
landed in.

### `cogos_resolve` calls a route the kernel no longer serves

`cogos_resolve` sends `GET {COG_OS_BASE_URL}/resolve`, a bare path with no
`/v1/` prefix. The current kernel does not register that route; it only
serves `GET /v1/resolve` and `GET /v1/uri/resolve`
(`internal/engine/serve.go` in `myrgic/cogos`). Every call to
`cogos_resolve` against a current kernel returns a 404.

Treat `cogos_resolve` as deprecated until it is updated to call
`/v1/resolve`: do not rely on it, and do not route new work through it. The
other thirteen bridge tools were checked against the same kernel route table
and are current. Fixing `cogos_resolve` is a small code change (swap the
request path in `src/cog_sandbox_mcp/tools/cogos_bridge.py`) and is tracked
separately from this documentation pass.
