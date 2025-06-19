from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("mu_mcp")


mu_query_man = open("mu_mcp/mu-query.txt", "r").read().strip()


# Add MCP health check tool
@mcp.tool("health_check")
def health_check() -> str:
    """Health check for the MCP server."""
    return "ok"


# @mcp.prompt(name="Search Emails")
# def create_query(query: str) -> str:
#     return f"Given the following query, create a mu search command.Query:\n\n{query}\n\nmu manual: {mu_query_man}"


@mcp.resource("resource://query-manual", name="Query Manual")
def get_manual() -> str:
    """Man page for using mu query"""
    return mu_query_man


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
