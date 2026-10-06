
# mu-mcp: MCP Server for the `mu` Mail Indexer

[![PyPI](https://img.shields.io/pypi/v/mu-mcp?color=blue)](https://pypi.org/project/mu-mcp/)
[![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fdanielfleischer%2Fmu-mcp%2Fmaster%2Fpyproject.toml&color=yellow)](https://github.com/danielfleischer/mu-mcp/blob/master/pyproject.toml)
[![GitHub release](https://img.shields.io/github/v/release/danielfleischer/mu-mcp?color=orange)](https://github.com/danielfleischer/mu-mcp/releases)
[![MCP](https://img.shields.io/badge/MCP-server-blueviolet)](https://modelcontextprotocol.io)
[![GitHub license](https://img.shields.io/github/license/danielfleischer/mu-mcp?color=red)](https://github.com/danielfleischer/mu-mcp/blob/master/LICENSE)

A Model Context Protocol (MCP) server for querying your local [`mu`](https://github.com/djcb/mu) mail index. This server enables fast, structured mail search from Claude Desktop and other MCP clients.

<img src="assets/claude-screenshot.png" width="500"/>

## Features

- **Stdio MCP server** for easy integration
- **Tools:** `search_emails`, `view_emails` (HTML-only emails converted to text), `view_thread` (reads a conversation from one message), `find_contacts` (resolves names to email addresses), `list_attachments`, `open_attachment` (saves to a temp dir and optionally opens with the default OS viewer), and `mu_help` for the full `mu` reference on demand.
- **Small context footprint:** a short query guide lives in the tool description; the full man pages are only loaded when the model asks for them.
- **Fast, flexible mail search** using the `mu` index
- **Claude Desktop ready**: simple installation and config
- **Python, uv, and MCP SDK** based

## Installation

Requires [`mu`](https://github.com/djcb/mu) installed and your mail indexed (`mu init` + `mu index`).

With [uv](https://github.com/astral-sh/uv) installed, run the published package
from PyPI without cloning the repository:

```sh
uvx mu-mcp
```

## Usage

### Run the MCP Server

```sh
uvx mu-mcp
```

The server communicates over stdio; normally your MCP client launches it using
the configuration below.

### Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
"mcpServers": {
  "email": {
    "command": "uvx",
    "args": ["mu-mcp"]
  }
}
```

The client needs `uvx` and `mu` on its PATH. If it cannot find `uvx`, use the
absolute path returned by `which uvx` as the command.

### Claude Code Integration

```sh
claude mcp add email -s user -- uvx mu-mcp
```

Use `-s local` instead to enable it only in the current project. Check it with `/mcp` in a new session.

## Query

Ask Claude to find emails, e.g. "Find emails with a PDF attachment that were sent last April and open the PDF", "Show me the email I received from Alice last week", or "Find emails with the subject 'Meeting Notes'".

To read a conversation, pass any message path from `search_emails` to
`view_thread(path)`. It returns indexed messages oldest first, omits duplicate
Message-IDs, and converts HTML-only bodies to text. The defaults are 30 messages
and 20,000 characters per message; increase `max_results` or `max_chars` if the
output is truncated.

Use `find_contacts("Alice")` to resolve a name before searching. Its pattern is
a case-insensitive regular expression matching names or addresses, such as
`@example\.com$`. An empty pattern lists contacts. Results default to 30 contacts;
use `max_results` to change the limit, or `personal=True` to restrict results to
contacts seen in messages involving your personal addresses configured in `mu`.

## Development

To run from a local checkout:

```sh
git clone https://github.com/danielfleischer/mu-mcp.git
cd mu-mcp
uv sync
uv run mu-mcp
```

- [x] Adding a tool to view an email.
- [x] Adding a tool to find and download attachments.
- [x] Progressive disclosure of the `mu` man pages via `mu_help`.
- [x] Add a `mu-mcp` console script and use `uvx mu-mcp` as the install method.
- [x] Describe when to use the server in its instructions, including email, inbox, messages, receipts, and attachments.
- [x] `view_thread`: show a whole conversation from one message.
- [x] `find_contacts` via `mu cfind`, to resolve a name to its addresses.

Run the tests with `uv run python -m unittest discover -s tests`. Integration
tests use an isolated temporary mail index and are skipped if `mu` is unavailable.

### Future ideas

- [ ] Return attachment text (PDF, DOCX) from `open_attachment`; Claude Desktop can't read the saved file paths.
