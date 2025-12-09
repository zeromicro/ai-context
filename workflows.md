# AI Workflows

## 1. New API Service

```
1. Ask requirements
2. create_api_spec
3. Show spec, get approval
4. create_api_service
5. generate_api_from_spec
6. Implement logic
7. Generate tests
8. Generate README.md (service overview, API docs, usage examples)
9. Generate API.md (detailed endpoint documentation)
```

## 2. New RPC Service

```
1. Ask requirements
2. create_rpc_service
3. Show proto
4. Implement methods
5. Generate tests
6. Generate README.md (service overview, proto docs, usage examples)
7. Generate RPC.md (detailed method documentation)
```

## 3. Database Model

```
1. Get DB type and connection
2. generate_model
3. Add to ServiceContext
4. Use in logic
```

## 4. Modify API

```
1. Edit .api file
2. validate_input
3. generate_api_from_spec
4. Update logic
5. Update tests
```

## 5. Add Auth

```
1. Add JWT config
2. Create login endpoint (generate token)
3. Add @server(jwt: Auth) to protected routes
4. Access userId from context
```

## 6. Add Caching

```
1. Add cache config
2. generate_model with cache=true
3. Use cache.CacheConf in config
```

## 7. Add Validation

```
1. Add validate tags to types
2. Add Validator to ServiceContext
3. Call Validator.StructCtx in logic
```

## Decision Matrix

| Request | Workflow |
|---------|----------|
| Create API | 1 + 7 |
| Add database | 3 + 6 |
| Protect endpoint | 5 |
| Modify API | 4 |
| Add RPC | 2 |
