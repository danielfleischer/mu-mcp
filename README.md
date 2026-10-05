
# mu-mcp: MCP Server for the `mu` Mail Indexer

[![GitHub release](https://img.shields.io/github/v/release/danielfleischer/mu-mcp)](https://github.com/danielfleischer/mu-mcp/releases)
[![GitHub license](https://img.shields.io/github/license/danielfleischer/mu-mcp?color=blue)](https://github.com/danielfleischer/mu-mcp/blob/master/LICENSE)

A Model Context Protocol (MCP) server for querying your local [`mu`](https://github.com/djcb/mu) mail index. This server enables fast, structured mail search from Claude Desktop and other MCP clients.

<img src="assets/claude-screenshot.png" width="500"/>

## Features

- **Stdio MCP server** for easy integration
- **Tools:** `search_emails`, `view_emails` (HTML-only emails converted to text), `list_attachments`, `open_attachment` (saves to a temp dir and optionally opens with the default OS viewer), and `mu_help` for the full `mu` reference on demand.
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

### Future ideas

- [ ] Return attachment text (PDF, DOCX) from `open_attachment`; Claude Desktop can't read the saved file paths.
- [ ] `view_thread`: show a whole conversation from one message.
- [ ] `find_contacts` via `mu cfind`, to resolve a name to its addresses.
