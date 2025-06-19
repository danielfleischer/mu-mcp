# from typing import Any

# import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("mu_mcp")


# Add MCP health check tool
@mcp.tool("health_check")
def health_check() -> str:
    """Health check for the MCP server."""
    return "ok"


@mcp.tool("query")
def query(query: str) -> str:
    """Query the MCP server by running a shell command with the mu CLI tool."""
    import subprocess

    try:
        result = subprocess.run(
            ["mu", "find"] + query.split(), capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"
