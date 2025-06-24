from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("mu_mcp")


mu_query_man = open("mu_mcp/mu-query.txt", "r").read().strip()
mu_find_man = open("mu_mcp/mu-find.txt", "r").read().strip()
mu_extract_man = open("mu_mcp/mu-extract.txt", "r").read().strip()


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


query.__doc__ += "\n\n" + mu_find_man + mu_query_man

mcp.tool("query")(query)


@mcp.tool("view")
def view(paths: str) -> str:
    """
    View emails using `mu`, by providing their paths.

    ```
    mu view $paths
    ```

    Paths can be extracted using the following:
    ```
    mu find --fields "l" SOME_QUERY
    ```
    """
    import subprocess

    try:
        result = subprocess.run(
            ["mu", "view"] + paths.split(), capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"


def get_attachment(command: str) -> str:
    r"""
    Open attachments in email by providing the email path.

    The tool downloads the attachment into a temp dir and open it.

    The `command` includes the paths and the pattern of attachment files.

    The prefix `mu extract --target-dir /tmp --overwrite --play` SHOULD NOT appear in `command`.

    See the man page for `mu extract`.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["mu", "extract", "--target-dir", "/tmp", "--overwrite", "--play"] + command.split(),
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"


get_attachment.__doc__ += "\n\n" + mu_extract_man

mcp.tool("get_attachment")(get_attachment)


if __name__ == "__main__":
    mcp.run(transport="stdio")
