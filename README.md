# go-zero AI Context

English | [简体中文](#简体中文)

Project instructions and verified examples for building services with go-zero.
The workflow layer lives here; [zero-skills](https://github.com/zeromicro/zero-skills)
provides detailed reference material. Code generation uses goctl in the terminal.

## One-Prompt Setup

Tell your assistant:

```text
Set up go-zero AI context from https://github.com/zeromicro/ai-context.
Follow its README for my editor, preserve existing instructions, and verify
that the editor loads the installed rule and can read the referenced files.
```

Setup requires an editor-specific entrypoint. Cloning this repository alone does
not activate its instructions. If the assistant cannot identify your editor, tell
it which one you use.

## Manual Setup

Run from the consuming project's Git root. Add each submodule only once:

```bash
git submodule add https://github.com/zeromicro/ai-context.git .ai-context/go-zero
git submodule add https://github.com/zeromicro/zero-skills.git .ai-context/zero-skills
```

Then install the adapter for your editor below. Commands use `cp -n` to preserve
existing files. If the destination exists, merge the template into it manually;
a skipped copy does not install the adapter. Keep existing frontmatter valid.

### Claude Code

```bash
cp -n .ai-context/go-zero/adapters/CLAUDE.md CLAUDE.md
```

This imports the core instructions through `@.ai-context/go-zero/00-instructions.md`.
The referenced workflow and patterns are read when needed. For native zero-skills
discovery, optionally install it at `.claude/skills/zero-skills` instead of
`.ai-context/zero-skills` and adjust its reference in the adapter.
See [Claude memory and imports](https://code.claude.com/docs/en/memory).

### Codex and OpenCode

```bash
cp -n .ai-context/go-zero/adapters/AGENTS.md AGENTS.md
```

Codex discovers `AGENTS.md` from the project root toward the current working
directory, while OpenCode loads it as persistent project instructions. Start a
new session after installing or changing the file. See the documentation for
[Codex](https://developers.openai.com/codex/guides/agents-md/) and
[OpenCode](https://opencode.ai/docs/rules/).

### GitHub Copilot

```bash
mkdir -p .github
cp -n .ai-context/go-zero/adapters/copilot-instructions.md .github/copilot-instructions.md
```

See [Copilot repository instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions).

### Cursor

```bash
mkdir -p .cursor/rules
cp -n .ai-context/go-zero/adapters/go-zero.mdc .cursor/rules/go-zero.mdc
```

The adapter has `alwaysApply: true`. A directory named `.cursorrules` is not a
replacement for a rule file. See [Cursor rules](https://prod.cursor.com/docs/rules).

### Windsurf

```bash
mkdir -p .windsurf/rules
cp -n .ai-context/go-zero/adapters/go-zero.md .windsurf/rules/go-zero.md
```

The adapter has `trigger: always_on`. A directory named `.windsurfrules` is not
a rule file. See [Cascade rules](https://docs.windsurf.com/windsurf/cascade/memories).

### Verify Installation

1. Confirm the editor recognizes the installed entrypoint in its rules/instructions UI.
2. Start a new conversation and ask the assistant to read
   `.ai-context/go-zero/00-instructions.md` and name the verification steps in
   `.ai-context/go-zero/workflows.md`.
3. Confirm that `.ai-context/zero-skills/SKILL.md` is accessible when detailed
   references are needed. An explicit read checks accessibility; the editor UI
   check is still needed to confirm automatic loading.
4. Commit the adapters, `.gitmodules`, and submodule pointers together.

After cloning a consuming project, restore its pinned submodules:

```bash
git submodule update --init --recursive
```

## Usage

Examples of requests:

- Create a user management API with CRUD operations.
- Add JWT authentication and ownership checks.
- Add rate limiting and circuit breakers.
- Review handler code for go-zero anti-patterns.

The entrypoint directs the assistant to [workflows.md](workflows.md),
[tools.md](tools.md), and [patterns.md](patterns.md). Use existing project
conventions; contract changes start with `.api` or `.proto`, while implementation
changes need no regeneration.

## Updating

Update only the context submodules, then review and commit their new pointers:

```bash
git submodule update --init .ai-context/go-zero .ai-context/zero-skills
git submodule update --remote .ai-context/go-zero .ai-context/zero-skills
git diff --submodule
```

Adapters are copied files. Compare updated templates with your installed adapters
and merge changes while preserving project-specific instructions. Existing
installations under older paths can remain there if adapter references are adjusted.

## Requirements

The verification baseline is Go 1.26.3, goctl 1.9.2, and go-zero 1.9.2.
This is a reproducible baseline, not a claim that these are the latest versions.
Existing projects should retain their selected versions unless intentionally upgraded.

```bash
go install github.com/zeromicro/go-zero/tools/goctl@v1.9.2
```

Git is required for submodules. RPC generation additionally requires protoc and
the Go protobuf/gRPC plugins; see [tools.md](tools.md).

## Verification

Maintainers can run the same checks as CI:

```bash
python3 scripts/check_docs.py
python3 -B -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_docs.py --online
python3 scripts/verify_patterns.py
```

The offline documentation check validates local links, fences, whitespace, and
adapter paths/frontmatter. Regression tests ensure disabled adapter settings,
broken links, and malformed fences fail the check. The optional online check verifies external link
availability (not remote anchors). Pattern verification uses temporary directories,
extracts the marked examples from Markdown, generates API code and a MySQL model,
then builds and tests the completed service. It also checks API scaffold creation
and preservation of custom handlers/logic during regeneration. Configuration tests
load the documented YAML and verify environment-variable expansion.

Python 3.10+, Go, and goctl are required. Go dependency downloads and online link
checks need network access. Tests use a fake model and an HTTP test server, so
MySQL and Redis are not required. RPC generation is documented but is not covered
by this API fixture.

## Related Projects

- [go-zero](https://github.com/zeromicro/go-zero)
- [zero-skills](https://github.com/zeromicro/zero-skills)

## License

MIT License — same as the go-zero framework.

## 简体中文

本仓库提供 go-zero 工作流、工具说明和可验证的代码示例。
[zero-skills](https://github.com/zeromicro/zero-skills) 提供详细参考资料。
仅克隆仓库不会自动启用指令，还需要安装编辑器对应的入口文件。

### 安装

在项目的 Git 根目录添加两个子模块（已有则跳过）：

```bash
git submodule add https://github.com/zeromicro/ai-context.git .ai-context/go-zero
git submodule add https://github.com/zeromicro/zero-skills.git .ai-context/zero-skills
```

按上方对应编辑器章节复制适配文件：

| 编辑器 | 模板（位于 adapters/） | 项目内目标路径 |
|--------|-----------------------|----------------|
| Claude Code | CLAUDE.md | CLAUDE.md |
| Codex | AGENTS.md | AGENTS.md |
| OpenCode | AGENTS.md | AGENTS.md |
| GitHub Copilot | copilot-instructions.md | .github/copilot-instructions.md |
| Cursor | go-zero.mdc | .cursor/rules/go-zero.mdc |
| Windsurf | go-zero.md | .windsurf/rules/go-zero.md |

复制命令使用 `cp -n` 保留已有文件。如果目标已存在，请手动合并模板并保留原有配置；
跳过复制不代表安装成功。Claude 模板使用导入语法，OpenCode 使用项目根目录的
`AGENTS.md`，Cursor/Windsurf 模板包含自动加载配置。
不要把仓库作为目录安装到 `.cursorrules` 或 `.windsurfrules`。

在编辑器界面确认规则已加载，再开启新对话，要求助手读取
`.ai-context/go-zero/00-instructions.md` 并列出工作流中的验证步骤。
显式读取只能确认文件可访问，自动加载仍需通过编辑器确认。
提交适配文件、`.gitmodules` 和子模块指针。克隆项目后运行
`git submodule update --init --recursive` 恢复固定版本。

### 更新与验证

按上方 Updating 章节仅更新这两个子模块，并检查差异。
适配文件为复制件，更新后需比较模板并合并变化，保留项目已有指令。

验证基线为 Go 1.26.3、goctl 1.9.2 和 go-zero 1.9.2，并非声明它们是最新版本。
已有项目保留原有版本。RPC 还需要 protoc 及 Go 插件，详见 [tools.md](tools.md)。

维护者运行 Verification 章节的命令，检查文档链接、适配文件以及
Markdown 中的实际代码。验证会生成 API 和 MySQL 模型，构建服务并执行测试；
回归测试确认错误的适配配置、链接和代码围栏会被拒绝，并验证 YAML 环境变量展开。
测试使用假模型，无需启动 MySQL 或 Redis。在线链接检查和依赖下载需要网络。
当前示例验证不覆盖 RPC 生成。
