from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("mu_mcp")


mu_query_man = open("mu_mcp/mu-query.txt", "r").read().strip()


# Add MCP health check tool
@mcp.tool("health_check")
def health_check() -> str:
    """Health check for the MCP server."""
    return "ok"


def query(query: str) -> str:
    """
    Query `mu` by providing a valid query to be sent in the following way

    ```
    mu find $query
    ```

    Here is the syntax guide for mu queries.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["mu", "find"] + query.split(), capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"


query.__doc__ += "\n\n" + mu_query_man

mcp.tool("query")(query)

if __name__ == "__main__":
    mcp.run(transport="stdio")
