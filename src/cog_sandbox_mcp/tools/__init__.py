from mcp.server.fastmcp import FastMCP

from cog_sandbox_mcp.tools import authorization, cogos_bridge, dedup, fs, seat


def register_all(mcp: FastMCP) -> None:
    authorization.register(mcp)
    fs.register(mcp)
    dedup.register(mcp)
    # Bridge tools register themselves only if COG_OS_BASE_URL is set at startup.
    cogos_bridge.register(mcp)
    # Seat tools register themselves only if COG_SANDBOX_SEATS_ENABLED is set.
    seat.register(mcp)
