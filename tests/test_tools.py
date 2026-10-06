import asyncio
import os
import shutil
import subprocess
import tempfile
import unittest
from email.message import EmailMessage
from pathlib import Path
from unittest.mock import patch

from mu_mcp.mu_mcp import find_contacts, mcp, view_thread


class ToolErrorTests(unittest.TestCase):
    def test_thread_validation(self):
        with patch("mu_mcp.mu_mcp.run_mu") as run:
            self.assertIn("Error:", view_thread(""))
            self.assertIn("Error:", view_thread("/mail/message", max_results=0))
            self.assertIn("Error:", view_thread("/mail/message", max_chars=-1))
            run.assert_not_called()

    def test_contact_validation(self):
        with patch("mu_mcp.mu_mcp.run_mu") as run:
            self.assertIn("Error:", find_contacts("Alice", max_results=0))
            run.assert_not_called()

    def test_thread_errors(self):
        with patch("mu_mcp.mu_mcp.run_mu", return_value=(19, "", "database locked")):
            self.assertIn("Error finding thread: database locked", view_thread("/mail/message"))
        for result in [(2, "", "no matches"), (0, "", "")]:
            with self.subTest(result=result):
                with patch("mu_mcp.mu_mcp.run_mu", return_value=result):
                    self.assertIn("No thread found", view_thread("/mail/message"))

    def test_contact_errors(self):
        with patch("mu_mcp.mu_mcp.run_mu", return_value=(99, "", "invalid regexp")):
            self.assertIn("Error finding contacts: invalid regexp", find_contacts("["))
        for result in [(2, "", "no matches"), (0, "", "")]:
            with self.subTest(result=result):
                with patch("mu_mcp.mu_mcp.run_mu", return_value=result):
                    self.assertIn("No contacts found", find_contacts("Alice"))

    def test_thread_continues_after_unreadable_message(self):
        def fake_mu(args):
            if args[0] == "find":
                return 0, "/mail/gone\n/mail/readable", ""
            if args[1] == "/mail/gone":
                return 1, "", "file missing"
            return 0, "Readable body", ""

        with patch("mu_mcp.mu_mcp.run_mu", side_effect=fake_mu):
            result = view_thread("/mail/gone")
        self.assertIn("Error viewing /mail/gone: file missing", result)
        self.assertIn("Readable body", result)

    def test_tools_registered_with_mcp(self):
        tools = {tool.name: tool for tool in asyncio.run(mcp.list_tools())}
        self.assertEqual(tools["view_thread"].inputSchema["required"], ["path"])
        self.assertEqual(tools["find_contacts"].inputSchema["required"], ["pattern"])
        self.assertEqual(tools["view_thread"].inputSchema["properties"]["max_results"]["default"], 30)
        self.assertFalse(tools["find_contacts"].inputSchema["properties"]["personal"]["default"])


@unittest.skipUnless(shutil.which("mu"), "mu is not installed")
class MailIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="mu_mcp_tests_")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        maildir = cls.root / "Mail with spaces"
        for folder in ["cur", "new", "tmp"]:
            (maildir / folder).mkdir(parents=True)
        cls.paths = {}
        fixtures = [
            ("root", "root:2,S", "Alice Example <alice@example.com>", "Opening body", [], False),
            ("reply", 'reply "quoted" \\ name:2,S', "Bob Example <bob@example.com>", "Reply body", ["root"], False),
            ("branch", "branch:2,S", "Alice Example <alice@work.example>", "Branch body", ["root"], False),
            ("html", "html:2,S", "Bob Example <bob@example.com>", "<p>HTML leaf body</p>", ["root", "reply"], True),
            ("unrelated", "unrelated:2,S", "List Only <list@example.org>", "Unrelated body", [], False),
            ("standalone", "standalone:2,S", "List Only <list@example.org>", "Standalone body", [], False),
        ]
        for day, (key, filename, sender, body, refs, html) in enumerate(fixtures, 1):
            msg = EmailMessage()
            msg["From"] = sender
            msg["To"] = "Me <me@example.net>" if key not in {"unrelated", "standalone"} else "other@example.org"
            msg["Subject"] = "Conversation"  # Same subject alone must not join threads.
            msg["Date"] = f"{day:02d} Jan 2025 10:00:00 +0000"
            msg["Message-ID"] = f"<{key}@test.example>"
            if refs:
                msg["References"] = " ".join(f"<{ref}@test.example>" for ref in refs)
                msg["In-Reply-To"] = f"<{refs[-1]}@test.example>"
            msg.set_content(body, subtype="html" if html else "plain")
            path = maildir / "cur" / filename
            path.write_bytes(msg.as_bytes())
            cls.paths[key] = str(path)
            if key == "root":
                (maildir / "cur" / "duplicate:2,S").write_bytes(msg.as_bytes())

        env_patch = patch.dict(os.environ, {"MUHOME": str(cls.root / "index"), "NO_COLOR": "1"})
        env_patch.start()
        cls.addClassCleanup(env_patch.stop)
        for args in [
            ["init", "--maildir", str(maildir), "--personal-address", "me@example.net"],
            ["index"],
        ]:
            completed = subprocess.run(["mu", *args], capture_output=True, text=True)
            if completed.returncode:
                raise RuntimeError(f"mu {args[0]} failed: {completed.stderr}")

    def test_thread_from_any_message_includes_branches_and_html(self):
        for key in ["root", "reply", "branch", "html"]:
            with self.subTest(seed=key):
                result = view_thread(self.paths[key])
                bodies = ["Opening body", "Reply body", "Branch body", "HTML leaf body"]
                positions = [result.index(body) for body in bodies]
                self.assertEqual(positions, sorted(positions))
                for body in bodies:
                    self.assertEqual(result.count(body), 1)
                self.assertNotIn("Unrelated body", result)
                self.assertNotIn("Standalone body", result)
                self.assertNotIn("<p>", result)
                self.assertIn(f"Path: {self.paths['reply']}", result)
                self.assertNotIn("Showing first", result)

    def test_standalone_message(self):
        result = view_thread(self.paths["standalone"])
        self.assertIn("Standalone body", result)
        self.assertEqual(result.count("Path: "), 1)

    def test_missing_path(self):
        self.assertIn("No thread found", view_thread(str(self.root / "missing")))

    def test_thread_limits(self):
        result = view_thread(self.paths["html"], max_results=2)
        self.assertIn("Opening body", result)
        self.assertIn("Reply body", result)
        self.assertNotIn("Branch body", result)
        self.assertIn("Showing first 2 messages", result)
        self.assertNotIn("Showing first", view_thread(self.paths["root"], max_results=4))
        result = view_thread(self.paths["root"], max_chars=10)
        self.assertEqual(result.count("Truncated at 10 chars"), 4)

    def test_resolve_name_to_multiple_addresses(self):
        result = find_contacts("aLiCe")
        self.assertIn("alice@example.com", result)
        self.assertIn("alice@work.example", result)
        self.assertNotIn("bob@example.com", result)
        self.assertNotIn("Showing first", result)

    def test_regex_and_personal_contacts(self):
        result = find_contacts(r"@example\.org$")
        self.assertIn("list@example.org", result)
        self.assertIn("other@example.org", result)
        self.assertIn("No contacts found", find_contacts(r"@example\.org$", personal=True))
        self.assertIn("alice@example.com", find_contacts("Alice", personal=True))

    def test_contact_limits_and_empty_pattern(self):
        result = find_contacts("Alice", max_results=1)
        self.assertIn("Showing first 1 contacts", result)
        self.assertEqual(len(result.split("\n\n")[0].splitlines()), 1)
        self.assertNotIn("Showing first", find_contacts("Alice", max_results=2))
        result = find_contacts("", max_results=2)
        self.assertIn("Showing first 2 contacts", result)
        self.assertEqual(len(result.split("\n\n")[0].splitlines()), 2)

    def test_contact_no_matches_invalid_regex_and_option_like_pattern(self):
        self.assertIn("No contacts found", find_contacts("nobody-here"))
        self.assertIn("Error finding contacts", find_contacts("["))
        self.assertIn("No contacts found", find_contacts("--personal"))


if __name__ == "__main__":
    unittest.main()
