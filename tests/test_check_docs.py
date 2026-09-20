"""Regression tests: broken documentation must fail the repository check."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_docs", ROOT / "scripts/check_docs.py")
check_docs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_docs)


class DocumentationChecks(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="ai-context-doc-test-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        for path in ROOT.glob("*.md"):
            shutil.copy2(path, self.root / path.name)
        shutil.copytree(ROOT / "adapters", self.root / "adapters")

    def append(self, name, text):
        path = self.root / name
        path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")

    def check(self, expected_error=None):
        output = io.StringIO()
        with patch.object(check_docs, "ROOT", self.root), \
                patch("sys.argv", ["check_docs.py"]), \
                redirect_stdout(output), redirect_stderr(output):
            if expected_error:
                with self.assertRaises(SystemExit) as caught:
                    check_docs.main()
                self.assertEqual(caught.exception.code, 1)
            else:
                check_docs.main()
        if expected_error:
            self.assertIn(expected_error, output.getvalue())

    def test_current_documents_pass(self):
        self.check()

    def test_activation_in_body_does_not_override_disabled_frontmatter(self):
        for name, enabled, disabled in (
            ("go-zero.mdc", "alwaysApply: true", "alwaysApply: false"),
            ("go-zero.md", "trigger: always_on", "trigger: manual"),
        ):
            with self.subTest(adapter=name):
                path = self.root / "adapters" / name
                original = path.read_text(encoding="utf-8")
                path.write_text(original.replace(enabled, disabled) + "\n" + enabled + "\n",
                                encoding="utf-8")
                self.check("expected exactly one frontmatter field")
                path.write_text(original, encoding="utf-8")

    def test_commented_activation_is_rejected(self):
        path = self.root / "adapters/go-zero.mdc"
        text = path.read_text(encoding="utf-8").replace("alwaysApply: true", "# alwaysApply: true")
        path.write_text(text, encoding="utf-8")
        self.check("expected exactly one frontmatter field")

    def test_duplicate_activation_is_rejected(self):
        path = self.root / "adapters/go-zero.mdc"
        text = path.read_text(encoding="utf-8").replace(
            "alwaysApply: true", "alwaysApply: true\nalwaysApply: false"
        )
        path.write_text(text, encoding="utf-8")
        self.check("expected exactly one frontmatter field")

    def test_broken_local_link_is_rejected(self):
        self.append("README.md", "\n[Missing](missing.md)\n")
        self.check("missing local link")

    def test_broken_anchor_is_rejected(self):
        self.append("README.md", "\n[Missing](patterns.md#missing-section)\n")
        self.check("missing anchor")

    def test_unclosed_fence_is_rejected(self):
        self.append("README.md", "\n```go\npackage example\n")
        self.check("unclosed code fence")

    def test_links_inside_nested_code_fences_are_ignored(self):
        self.append("README.md", "\n````markdown\n```text\n[Example](missing.md)\n```\n````\n")
        self.check()

    def test_unicode_anchor_is_recognized(self):
        self.append("README.md", "\n### 验证示例\n\n[示例](#验证示例)\n")
        self.check()


if __name__ == "__main__":
    unittest.main()
