#!/usr/bin/env python3
"""Build and test the exact examples in patterns.md, outside the worktree."""

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GOCTL_VERSION = "1.9.2"
GO_ZERO_VERSION = "v1.9.2"
VALIDATOR_VERSION = "v10.26.0"


def run(*args, cwd, env):
    print("+", " ".join(args), flush=True)
    return subprocess.run(args, cwd=cwd, env=env, check=True)


def main():
    for tool in ("go", "goctl", "gofmt"):
        if not shutil.which(tool):
            raise SystemExit(f"Missing {tool}; see README.md requirements")
    version = subprocess.check_output(["goctl", "--version"], text=True)
    if not re.search(rf"\b{re.escape(GOCTL_VERSION)}\b", version):
        raise SystemExit(f"Expected goctl {GOCTL_VERSION}, got {version.strip()}")

    text = (ROOT / "patterns.md").read_text(encoding="utf-8")
    blocks = re.findall(
        r"<!-- verify: ([\w/.-]+) -->\n```\w+\n(.*?)\n```", text, re.DOTALL
    )
    if not blocks or len(blocks) != text.count("<!-- verify:"):
        raise SystemExit("Missing or malformed verification blocks")
    paths = [path for path, _ in blocks]
    if len(set(paths)) != len(paths):
        raise SystemExit("Duplicate verification paths")

    with tempfile.TemporaryDirectory(prefix="ai-context-verify-") as directory:
        work = Path(directory).resolve()
        service = work / "service"
        service.mkdir()
        # goctl 1.9.2 treats GOWORK=off as an active workspace. Let Go discover
        # the standalone temporary module instead of inheriting a caller's workspace.
        env = dict(os.environ, GOWORK="")
        env.setdefault("GOCACHE", str(work / "go-build"))
        templates = str(work / "templates")
        for path, source in blocks:
            target = service / path
            if not target.resolve().is_relative_to(service.resolve()):
                raise SystemExit(f"Unsafe verification path: {path}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source + "\n", encoding="utf-8")

        run("go", "mod", "init", "example.com/user", cwd=service, env=env)
        run("go", "mod", "edit", "-go=1.26.3",
            f"-require=github.com/zeromicro/go-zero@{GO_ZERO_VERSION}",
            f"-require=github.com/go-playground/validator/v10@{VALIDATOR_VERSION}",
            cwd=service, env=env)
        run("goctl", "api", "validate", "-api", "user.api", cwd=service, env=env)
        generate = ("goctl", "api", "go", "-api", "user.api", "-dir", ".",
                    "--style", "go_zero", "--home", templates)
        # Generate first, then install the documented custom implementation.
        # Start with only the contracts, so accidental filename mismatches fail builds.
        for path, _ in blocks:
            if path.endswith(".go"):
                (service / path).unlink()
        run(*generate, cwd=service, env=env)
        run("goctl", "model", "mysql", "ddl", "-src", "user.sql", "-dir",
            "internal/model", "--style", "go_zero", "--home", templates,
            cwd=service, env=env)
        for path, source in blocks:
            target = service / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source + "\n", encoding="utf-8")
        shutil.copytree(ROOT / "tests" / "patterns", service, dirs_exist_ok=True)
        custom = {path: (service / path).read_bytes() for path in paths
                  if path.endswith(".go")}
        run(*generate, cwd=service, env=env)
        for path, source in custom.items():
            if (service / path).read_bytes() != source:
                raise SystemExit(f"Regeneration changed custom file: {path}")
        go_files = [str(p) for p in service.rglob("*.go")]
        run("gofmt", "-w", *go_files, cwd=service, env=env)
        run("go", "mod", "tidy", cwd=service, env=env)
        run("go", "build", "./...", cwd=service, env=env)
        run("go", "test", "-count=1", "./...", cwd=service, env=env)

        # Verify the api-new recipe uses the generated service directory.
        run("goctl", "api", "new", "scaffold", "--style", "go_zero",
            "--home", templates, cwd=work, env=env)
        scaffold = work / "scaffold"
        if not (scaffold / "go.mod").is_file():
            raise SystemExit("api new did not create a service module")
        run("go", "mod", "edit",
            f"-require=github.com/zeromicro/go-zero@{GO_ZERO_VERSION}",
            cwd=scaffold, env=env)
        run("go", "mod", "tidy", cwd=scaffold, env=env)
        run("go", "build", "./...", cwd=scaffold, env=env)
        run("go", "test", "./...", cwd=scaffold, env=env)
    print("Pattern generation, regeneration, build, and behavior tests passed.")


if __name__ == "__main__":
    main()
