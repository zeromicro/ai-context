# AI Instructions for go-zero

## File Priority

Paths below are relative to this file, not the consuming project's root.
Read the workflow for the current task, then its tools and patterns as needed.
Preserve the consuming project's conventions and existing instructions.

1. `workflows.md` - Task patterns
2. `tools.md` - goctl commands
3. `patterns.md` - Code patterns
4. [zero-skills](https://github.com/zeromicro/zero-skills) - Detailed patterns (查阅详细模式)

## Rules

### Spec-First

- Create or update `.api` before changing REST contracts; use `.proto` for RPC contracts
- For business-logic-only changes, edit implementation and tests without regenerating contracts
- Write spec following patterns in `patterns.md`
- Validate REST specs with `goctl api validate -api <file>.api`

### Tool Usage

- Use goctl commands in terminal, NOT manual code generation
- `goctl api new` for demo scaffolds; use `goctl api go` for the actual API contract
- `goctl rpc new` / `goctl rpc protoc` for new RPC services
- `goctl api go` for code from spec
- `goctl model mysql/pg/mongo` for database models
- Run commands from the service's module directory; preserve the existing module path and naming style
- After implementation: format changed Go files → `go mod tidy` → verify imports → `go build ./...` → `go test ./...`
- If goctl is missing, use the project's pinned version; this repository verifies `go install github.com/zeromicro/go-zero/tools/goctl@v1.9.2`

### Implementation

- Generate FULL implementation, not stubs
- Fill logic layer with business code
- Add validation tags and wire `go-playground/validator/v10`; tags alone do not run validation
- Add and run tests for changed behavior

### Documentation

- ALWAYS generate README.md for new services
  - Service overview and purpose
  - API/RPC endpoint documentation
  - Configuration guide
  - Usage examples with curl/grpcurl
  - Testing instructions
- Generate API.md/RPC.md for detailed endpoint docs
- Include request/response examples
- Document error codes and handling

### Go-Zero Conventions

- Context first: `func(ctx context.Context, req *types.Request)`
- Errors: use the project's error type and HTTP mapping; see the local `apperror` example in `patterns.md`
- Log internal failures with context; return generic messages to clients
- Config: `json:",default=value"`
- Validation: `validate:"required,min=3"`

## Decision Tree

```text
User Request →
├─ New API? → Write/validate .api → goctl api go → Implement → Verify → Document
├─ New RPC? → Write .proto → goctl rpc protoc → Implement → Verify → Document
├─ Database? → goctl model mysql/pg/mongo → Wire model → Verify
└─ Modify? → Contract changed? Regenerate from .api/.proto → Implement → Verify → Update docs
```

## Detailed Patterns

For complete implementation patterns, refer to [zero-skills](https://github.com/zeromicro/zero-skills):

Prefer the local knowledge-base path provided by the editor adapter; the links
below are fallbacks when the reference is not installed locally.

- REST API → [rest-api-patterns.md](https://github.com/zeromicro/zero-skills/blob/main/references/rest-api-patterns.md)
- RPC Services → [rpc-patterns.md](https://github.com/zeromicro/zero-skills/blob/main/references/rpc-patterns.md)
- Database → [database-patterns.md](https://github.com/zeromicro/zero-skills/blob/main/references/database-patterns.md)
- Resilience → [resilience-patterns.md](https://github.com/zeromicro/zero-skills/blob/main/references/resilience-patterns.md)
- goctl Commands → [goctl-commands.md](https://github.com/zeromicro/zero-skills/blob/main/references/goctl-commands.md)
- Troubleshooting → [common-issues.md](https://github.com/zeromicro/zero-skills/blob/main/troubleshooting/common-issues.md)

## Avoid

- Empty stubs
- Missing validation
- Returning raw internal errors to clients (wrapping errors internally with `fmt.Errorf` is fine)
- Editing generated model files; put custom queries in the generated extension file
- Missing context
- Skipping post-generation steps (mod tidy, build verify)
- Mismatched `--style` flag with existing code
