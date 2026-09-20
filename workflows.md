# AI Workflows

Use the existing project's module path, dependencies, and goctl naming style.
Clarify missing requirements that affect behavior; proceed when requirements are
already clear. Review contract changes with the user when their choices are needed.

## 1. New API Service

1. Write the `.api` contract using [patterns.md](patterns.md).
2. Run `goctl api validate -api <file>.api`.
3. Initialize a Go module if needed, then generate with
   `goctl api go -api <file>.api -dir . --style go_zero`.
4. Implement business logic, dependencies, validation, and error mapping.
5. Add behavior tests, including invalid inputs and dependency failures.
6. Run the verification checklist below after implementation.
7. Write README.md and API.md with configuration, endpoints, errors, and examples.

## 2. New RPC Service

1. Write the `.proto` contract, including `go_package`.
2. Check Go, goctl, protoc, protoc-gen-go, and protoc-gen-go-grpc prerequisites
   in [tools.md](tools.md).
3. Initialize a Go module if needed. Generate with
   `goctl rpc protoc <file>.proto --go_out=. --go-grpc_out=. --zrpc_out=. --style go_zero`.
4. Implement methods and dependencies; use appropriate gRPC status codes.
5. Add behavior tests and run the verification checklist.
6. Write README.md and RPC.md with configuration and grpcurl examples.

## 3. Database Model

1. Identify the database and schema. Prefer a DDL file when a live database is unnecessary.
2. Generate the model using [tools.md](tools.md); enable caching only if requested or required.
3. Wire the generated model into ServiceContext with the matching constructor.
4. Implement custom queries in the model's extension file, preserving generated files.
5. Test success, not-found, and dependency failure paths; run verification.

## 4. Modify a Service

1. Inspect the contract, generated files, existing logic, tests, and naming style.
2. If the contract changes, edit and validate `.api` or edit `.proto`, then regenerate.
   Skip regeneration for implementation-only changes.
3. Inspect the diff. Existing handler/logic files are preserved, so update their
   signatures, imports, and behavior to match changed request/response types.
4. Update tests and documentation; run verification after the final code change.

## 5. Add Auth

1. Add Auth configuration and supply a secret through the deployment's secret mechanism.
2. Implement login with credential verification, expiry, and a numeric `userId` JWT claim.
3. Add `@server(jwt: Auth)` to protected routes; validate the spec and regenerate.
4. Extract claims safely using [patterns.md](patterns.md). Check resource ownership
   or permissions as well as authentication.
5. Test missing/invalid/expired tokens and unauthorized resource access; run verification.

## 6. Add Caching

1. Add cache configuration and regenerate the model with `-cache`.
2. Use `cache.CacheConf` in Config and update the model constructor in ServiceContext.
   Existing extension files may need manual constructor changes when switching modes.
3. Test cache misses, invalidation after writes, and dependency failures; run verification.

## 7. Add Validation

1. Add `validate` tags to the `.api` types; validate the spec and regenerate Go types.
2. Add `*validator.Validate` to ServiceContext and initialize it with `validator.New()`.
3. Call `Validator.StructCtx` in logic and map failures to a safe HTTP 400 response.
4. Test valid, missing, and malformed fields; run verification.

## Verification Checklist

Run in the affected service's module directory:

1. Format changed Go files with `gofmt -w <changed-files>`.
2. Run `go mod tidy` and verify imports match the module path.
3. Run `go build ./...`.
4. Run `go test ./...` and relevant integration tests.
5. Review the final diff, generated files, and documentation for unintended changes.

Report the commands run and any checks that could not run. Generating tests does
not count as running them.

## Decision Matrix

| Request | Workflow |
|---------|----------|
| Create API | 1 + 7 |
| Add database | 3 (plus 6 only when caching is needed) |
| Protect endpoint | 5 |
| Modify API or RPC | 4 |
| Add RPC | 2 |
