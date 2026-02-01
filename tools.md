# MCP Tools

## create_api_service
Create REST API service structure
```json
{
  "service_name": "user-api",
  "output_dir": "./services/user",
  "style": "go_zero"
}
```

## create_rpc_service
Create gRPC service structure
```json
{
  "service_name": "order-rpc",
  "output_dir": "./services/order",
  "style": "go_zero"
}
```

## generate_api_from_spec
Generate code from .api file
```json
{
  "api_file": "user.api",
  "output_dir": "./",
  "style": "go_zero"
}
```
Safe to re-run, won't overwrite custom logic.

## generate_model
Generate database model
```json
{
  "source_type": "mysql",
  "source": "user:pass@tcp(host:3306)/db",
  "table": "users",
  "output_dir": "./model",
  "style": "go_zero"
}
```
Types: `mysql`, `postgres`, `mongo`
Add `"cache": true` for caching

## create_api_spec
Generate .api from description
```json
{
  "description": "User CRUD with auth",
  "service_name": "user-api",
  "style": "go_zero"
}
```

## analyze_project
Analyze existing project
```json
{
  "project_path": "./services/user-api"
}
```

## generate_config_template
Generate config template
```json
{
  "service_type": "api",
  "output_path": "./etc/config.yaml"
}
```
Types: `api`, `rpc`, `combined`

## generate_template
Generate deployment templates
```json
{
  "template_type": "docker",
  "output_path": "./Dockerfile"
}
```
Types: `docker`, `k8s`, `middleware`, `error_handler`

## validate_input
Validate .api syntax
```json
{
  "api_file": "user.api"
}
```

## validate_config
Validate config.yaml
```json
{
  "config_path": "./etc/config.yaml",
  "service_type": "api"
}
```

## Tool Sequences

**New API**: create_api_service → create_api_spec → validate_input → generate_api_from_spec

**New RPC**: create_rpc_service → [edit proto] → generate

**Add DB**: generate_model → [add to context] → [use in logic]

**Deploy**: generate_template(docker) → generate_template(k8s)
