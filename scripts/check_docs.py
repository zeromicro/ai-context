#!/usr/bin/env python3
"""Lightweight checks for this repository's Markdown and adapter contracts."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urldefrag, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[[^\]]+\]\(([^\s)]+)\)")


def prose(path, errors):
    lines = path.read_text(encoding="utf-8").splitlines()
    fence = None
    result = []
    for number, line in enumerate(lines, 1):
        if line.rstrip() != line:
            errors.append(f"{path.relative_to(ROOT)}:{number}: trailing whitespace")
        match = re.match(r"^(`{3,}|~{3,})(.*)$", line)
        if match:
            marker, suffix = match.groups()
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence) and not suffix.strip():
                fence = None
            continue
        if fence is None:
            result.append(line)
    if fence:
        errors.append(f"{path.relative_to(ROOT)}: unclosed code fence")
    if not path.read_bytes().endswith(b"\n"):
        errors.append(f"{path.relative_to(ROOT)}: missing final newline")
    return "\n".join(result)


def anchors(text):
    seen = {}
    result = set()
    for title in re.findall(r"^#{1,6}\s+(.+)$", text, re.MULTILINE):
        slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        result.add(f"{slug}-{count}" if count else slug)
    return result


def check_url(url):
    for attempt in range(2):
        try:
            request = Request(url, headers={"User-Agent": "ai-context-doc-check/1.0"})
            with urlopen(request, timeout=20) as response:
                if response.status >= 400:
                    return f"{url}: HTTP {response.status}"
            return None
        except (HTTPError, URLError, TimeoutError, OSError) as err:
            if attempt:
                return f"{url}: {err}"
    return None


def check_activation(name, text, activation, errors):
    # These adapters intentionally use flat YAML scalar fields. Require the
    # activation key in frontmatter, not in a comment or example in the body.
    if name in ("go-zero.mdc", "go-zero.md"):
        match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
        if not match:
            errors.append(f"{name}: missing frontmatter")
            return
        key, expected = activation.split(": ", 1)
        values = re.findall(rf"^{re.escape(key)}:\s*([^\n]*)$", match[1], re.MULTILINE)
        if values != [expected]:
            errors.append(f"{name}: expected exactly one frontmatter field: {activation}")
    elif activation not in text.splitlines():
        errors.append(f"{name}: missing activation: {activation}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", help="also check external URLs")
    args = parser.parse_args()
    errors = []
    files = sorted(ROOT.glob("*.md")) + sorted((ROOT / "adapters").glob("*"))
    documents = {path: prose(path, errors) for path in files}
    urls = set()
    for path, text in documents.items():
        for link in LINK.findall(text):
            parsed = urlsplit(link)
            if parsed.scheme in ("http", "https"):
                urls.add(urldefrag(link)[0])
                continue
            if parsed.scheme:
                errors.append(f"{path.name}: unsupported link scheme: {link}")
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not target.is_relative_to(ROOT) or not target.is_file():
                errors.append(f"{path.name}: missing local link: {link}")
            elif parsed.fragment:
                target_text = documents.get(target)
                if target_text is None:
                    target_text = prose(target, errors)
                if unquote(parsed.fragment) not in anchors(target_text):
                    errors.append(f"{path.name}: missing anchor: {link}")

    adapters = {
        "CLAUDE.md": ("CLAUDE.md", "@.ai-context/go-zero/00-instructions.md"),
        "copilot-instructions.md": (".github/copilot-instructions.md", "# go-zero"),
        "go-zero.mdc": (".cursor/rules/go-zero.mdc", "alwaysApply: true"),
        "go-zero.md": (".windsurf/rules/go-zero.md", "trigger: always_on"),
    }
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for name, (destination, activation) in adapters.items():
        text = (ROOT / "adapters" / name).read_text(encoding="utf-8")
        check_activation(name, text, activation, errors)
        command = f"cp -n .ai-context/go-zero/adapters/{name} {destination}"
        if command not in readme:
            errors.append(f"README.md: missing adapter installation command: {command}")
        if ".ai-context/go-zero/00-instructions.md" not in text:
            errors.append(f"{name}: missing instruction entrypoint")
        if ".ai-context/zero-skills/SKILL.md" not in text:
            errors.append(f"{name}: missing knowledge reference")
        for reference in re.findall(r"\.ai-context/go-zero/([\w./-]+)", text):
            if not (ROOT / reference).is_file():
                errors.append(f"{name}: missing instruction file: {reference}")
    for name in ("workflows.md", "tools.md", "patterns.md"):
        if not (ROOT / name).is_file():
            errors.append(f"Missing referenced document: {name}")

    if args.online:
        with ThreadPoolExecutor(max_workers=4) as pool:
            errors.extend(error for error in pool.map(check_url, sorted(urls)) if error)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print(f"Checked {len(files)} documents, including {len(adapters)} adapters; local links and Markdown passed.")
    if args.online:
        print(f"Checked {len(urls)} external URLs (remote anchors are not checked).")


if __name__ == "__main__":
    main()
