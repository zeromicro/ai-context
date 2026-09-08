# goctl Tools

## Prerequisites

```bash
# Check goctl
which goctl && goctl --version

# Install if missing
go install github.com/zeromicro/go-zero/tools/goctl@v1.9.2
```

Verification baseline: Go 1.26.3, goctl 1.9.2, and go-zero 1.9.2.
Keep existing projects on their selected versions unless upgrading is part of the task.
Ensure `$(go env GOPATH)/bin` (or your configured GOBIN) is on PATH.

RPC generation also needs `protoc`, `protoc-gen-go`, and `protoc-gen-go-grpc`:

```bash
protoc --version
protoc-gen-go --version
protoc-gen-go-grpc --version
```

Install missing protoc using your platform's package manager, and pin the Go
plugins to versions compatible with the target project's protobuf/gRPC dependencies.

## create_api_service

Create REST API service with goctl

```bash
mkdir -p <output_dir> && cd <output_dir>
goctl api new <service_name> --style go_zero
cd <service_name>
go mod tidy
go build ./...
```

## create_rpc_service

Create gRPC service with goctl

```bash
mkdir -p <output_dir> && cd <output_dir>
goctl rpc new <service_name> --style go_zero
cd <service_name>
go mod tidy
go build ./...
```

Or from existing proto:

```bash
goctl rpc protoc <file>.proto --go_out=. --go-grpc_out=. --zrpc_out=. --style go_zero
go mod tidy
go build ./...
```

## generate_api_from_spec

Generate code from .api file.
Run inside the target module; initialize it with `go mod init <module>` if needed.

```bash
goctl api validate -api <file>.api
goctl api go -api <file>.api -dir . --style go_zero
go mod tidy
go build ./...
```

Existing handler/logic files are preserved. Generated types and routes may change;
review the diff and manually reconcile existing signatures after contract changes.

## generate_model

Generate database model from table

**MySQL (live DB):**

```bash
goctl model mysql datasource \
  -url "user:pass@tcp(host:3306)/db" \
  -table "<table>" -dir ./model --style go_zero
```

**MySQL (DDL file):**

```bash
goctl model mysql ddl -src <file>.sql -dir ./model --style go_zero
```

**With cache:** add `-cache` flag to any command above.

**PostgreSQL:**

```bash
goctl model pg datasource \
  -url "postgres://user:pass@host:5432/db?sslmode=disable" \
  -table "<table>" -dir ./model --style go_zero
```

**MongoDB:**

```bash
goctl model mongo -type <TypeName> -dir ./model --style go_zero
```

## validate_api_spec

Validate .api syntax

```bash
goctl api validate -api <file>.api
```

## analyze_project

Understand existing project structure

```bash
# Locate contracts and Go source without changing the project
rg --files -g '*.api' -g '*.proto' -g '*.go'
```

`goctl api doc -dir . -o <docs_dir>` generates Markdown files; it is a write
operation, not a route-listing command.

## generate_config_template

See [goctl-commands.md](https://github.com/zeromicro/zero-skills/blob/main/references/goctl-commands.md#6-config-templates) in zero-skills for config templates.

## generate_template

See [goctl-commands.md](https://github.com/zeromicro/zero-skills/blob/main/references/goctl-commands.md#7-deployment-templates) in zero-skills for Dockerfile, Kubernetes, and Docker Compose templates.

## Post-Generation Checklist

After EVERY goctl generation:

1. Enter the service module; use `go mod init <module>` only if no module exists
2. `go mod tidy` — resolve dependencies
3. Verify imports match go.mod module path
4. `go build ./...` — confirm code compiles
5. Check `--style` flag matches existing file naming convention
6. After implementing logic, format changed files, repeat tidy/build, and run `go test ./...`
