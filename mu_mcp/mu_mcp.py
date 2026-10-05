import re
import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

import html2text
from mcp.server.fastmcp import FastMCP

HERE = Path(__file__).parent

mcp = FastMCP(
    "email",
    instructions=(
        "Use this server when a request involves the user's email, inbox, "
        "email messages or conversations, receipts, invoices, or email attachments. "
        "It searches the user's local mail index and reads messages, including "
        "HTML-only email, and can list, save, and open attachments. "
        "Start with search_emails to find relevant messages, then pass their "
        "paths to view_emails to read them or to list_attachments and "
        "open_attachment to work with attached files. Call mu_help when the "
        "short query guide in search_emails isn't enough."
    ),
)

NO_PLAIN_TEXT = "[No plain text body found]"


def html_to_text(html: str) -> str:
    converter = html2text.HTML2Text()
    converter.body_width = 0  # don't hard-wrap lines
    converter.ignore_images = True
    converter.ignore_links = True  # marketing mail is mostly tracking URLs
    text = converter.handle(html)
    # drop invisible preheader padding and trailing whitespace
    text = re.sub(r"[\u200b-\u200f\u034f\u00ad\ufeff]", "", text).replace("\xa0", " ")
    lines = [line.rstrip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def run_mu(args: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(["mu", *args], capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


@mcp.tool()
def search_emails(
    query: str,
    max_results: int = 30,
    sort: Literal["date", "from", "subject", "size"] = "date",
    newest_first: bool = True,
    include_thread: bool = False,
) -> str:
    """Search the local mail index with a `mu` query.

    Returns one line per message: `date | from | subject | path`. Pass the
    path to view_emails or list_attachments.

    Query syntax (quote phrases with double quotes; no shell is involved):
    - Bare words search from/to/cc/subject/body: `invoice march`
    - Fields: from: to: cc: contact: (any address) subject: body:
      maildir: (e.g. maildir:/Inbox) list: tag: file: (attachment name)
      mime: (attachment type, e.g. mime:application/pdf, mime:image/*)
    - Dates: date:2024-04..2024-04, date:2w.. (last 2 weeks),
      date:..2023, date:today..  (units: h d w m y)
    - Flags: flag:attach flag:unread flag:flagged flag:replied flag:personal
      flag:list flag:calendar
    - Operators: and, or, not, parentheses; implicit `and` between terms.
    - Wildcard suffix: `budg*`. Regex: `subject:/re.?port/`
    - Names match words in the address too: from:alice, from:amazon

    Examples:
    - from:alice date:1w..
    - subject:"meeting notes"
    - mime:application/pdf and date:2025-04..2025-04
    - (from:bank or from:visa) and flag:unread
    - contact:bob and not flag:list

    Args:
        query: the mu query.
        max_results: cap on returned messages; raise it or narrow the query
            if the result is cut off.
        sort: field to sort by.
        newest_first: reverse sort order (newest/Z first).
        include_thread: also return other messages from matching threads.
    """
    args = ["find", "--fields", "d | f | s | l", "--skip-dups", "--sortfield", sort, "--maxnum", str(max_results)]
    if newest_first:
        args.append("--reverse")
    if include_thread:
        args.append("--include-related")
    try:
        terms = shlex.split(query)
    except ValueError as e:
        return f"Error parsing query ({e}); check quoting."
    code, out, err = run_mu(args + terms)
    if code == 2 or (code == 0 and not out):
        return "No matches. Try fewer terms, a wider date range, or bare words instead of field: prefixes."
    if code != 0:
        return f"Error: {err}\nSee mu_help('query') for the full syntax."
    lines = out.splitlines()
    if len(lines) >= max_results:
        out += f"\n\n[Showing first {max_results}; there may be more. Narrow the query or raise max_results.]"
    return out


def _view_one(path: str, max_chars: int) -> str:
    code, out, err = run_mu(["view", path])
    if code != 0:
        return f"Error viewing {path}: {err}"
    if NO_PLAIN_TEXT in out:
        code, html_out, _ = run_mu(["view", "--format=html", path])
        if code == 0:
            headers, _, html = html_out.partition("\n\n")
            out = headers + "\n\n" + html_to_text(html)
    if len(out) > max_chars:
        out = out[:max_chars] + f"\n\n[Truncated at {max_chars} chars of {len(out)}.]"
    return out


@mcp.tool()
def view_emails(paths: list[str], max_chars: int = 20000) -> str:
    """Read emails (headers + body as text) given paths from search_emails.

    HTML-only emails are converted to plain text.

    Args:
        paths: message file paths.
        max_chars: per-message cap on returned text.
    """
    return ("\n\n" + "=" * 40 + "\n\n").join(_view_one(p, max_chars) for p in paths)


@mcp.tool()
def list_attachments(path: str) -> str:
    """List the MIME parts (attachments, inline images, bodies) of one email."""
    code, out, err = run_mu(["extract", path])
    return out if code == 0 else f"Error: {err}"


@mcp.tool()
def open_attachment(path: str, pattern: str = ".*", open_in_viewer: bool = True) -> str:
    """Save attachments of an email to a temp dir, optionally opening them.

    Returns the saved file paths, so their contents can be read afterwards.

    Args:
        path: message file path.
        pattern: case-sensitive PCRE matched against attachment file names,
            e.g. `.*\\.pdf$` or `(?i)invoice`. Default: all attachments.
        open_in_viewer: also open each file with the OS default application.
    """
    target = tempfile.mkdtemp(prefix="mu_mcp_")
    args = ["extract", "--target-dir", target, "--overwrite"]
    if open_in_viewer:
        args.append("--play")
    code, _, err = run_mu(args + [path, pattern])
    if code != 0:
        return f"Error: {err}\nUse list_attachments to see the file names."
    files = sorted(str(p) for p in Path(target).iterdir())
    if not files:
        return "No attachment matched the pattern. Use list_attachments to see the file names."
    return "Saved:\n" + "\n".join(files)


@mcp.tool()
def mu_help(topic: Literal["query", "fields", "find", "extract"]) -> str:
    """Full mu reference, for when the short guide in search_emails isn't enough.

    Topics: query (complete query language), fields (live list of fields and
    flags), find (search options), extract (attachment handling).
    """
    if topic == "fields":
        code, out, err = run_mu(["info", "fields"])
        return out if code == 0 else f"Error: {err}"
    return (HERE / f"mu-{topic}.txt").read_text().strip()


def main() -> None:
    """Run the email MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
