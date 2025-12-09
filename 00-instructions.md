# AI Instructions for go-zero

## File Priority

1. `workflows.md` - Task patterns
2. `tools.md` - MCP tools
3. `patterns.md` - Code patterns
4. [zero-skills](https://github.com/zeromicro/zero-skills) - Detailed patterns (查阅详细模式)

## Rules

### Spec-First
- ALWAYS create `.api` spec before code
- Use `create_api_spec` tool
- Validate with `validate_input`

### Tool Usage
- Use mcp-zero tools, NOT manual generation
- `create_api_service` for new API services
- `create_rpc_service` for new RPC services
- `generate_api_from_spec` for code from spec
- `generate_model` for database models

### Implementation
- Generate FULL implementation, not stubs
- Fill logic layer with business code
- Add validation tags: `validate:"required,email"`
- Generate tests automatically

### Go-Zero Conventions
- Context first: `func(ctx context.Context, req *types.Request)`
- Errors: `errorx.NewCodeError(code, msg)`
- Config: `json:",default=value"`
- Validation: `validate:"required,min=3"`

## Decision Tree

```
User Request →
├─ New API? → create_api_service → generate_api_from_spec
├─ New RPC? → create_rpc_service
├─ Database? → generate_model
└─ Modify? → Edit .api → generate_api_from_spec
```

## Detailed Patterns

For complete implementation patterns, refer to [zero-skills](https://github.com/zeromicro/zero-skills):

- REST API → [rest-api-patterns.md](https://github.com/zeromicro/zero-skills/blob/main/references/rest-api-patterns.md)
- RPC Services → [rpc-patterns.md](https://github.com/zeromicro/zero-skills/blob/main/references/rpc-patterns.md)
- Database → [database-patterns.md](https://github.com/zeromicro/zero-skills/blob/main/references/database-patterns.md)
- Resilience → [resilience-patterns.md](https://github.com/zeromicro/zero-skills/blob/main/references/resilience-patterns.md)
- Troubleshooting → [common-issues.md](https://github.com/zeromicro/zero-skills/blob/main/troubleshooting/common-issues.md)

## Avoid

- Empty stubs
- Missing validation
- `fmt.Errorf` for API errors (use `errorx.NewCodeError`)
- Manual SQL (use `generate_model`)
- Missing context
