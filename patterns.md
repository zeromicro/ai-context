# Code Patterns

The blocks marked `verify: path` form one runnable service with module path
`example.com/user`. [Verification](README.md#verification) extracts these exact
blocks, generates handlers/types/models with goctl, and tests the implementation.
Replace the example module path with your project's path.

## API Contract

This endpoint returns the authenticated user's record. Validation tags require an
explicit validator call; they are not automatically enforced by adding tags.

<!-- verify: user.api -->
```api
syntax = "v1"

type GetUserRequest {
    Id int64 `path:"id" validate:"min=1"`
}

type UserResponse {
    Id int64 `json:"id"`
    Email string `json:"email"`
}

@server(
    jwt: Auth
    group: user
)
service user-api {
    @handler getUser
    get /api/users/:id (GetUserRequest) returns (UserResponse)
}
```

For a create endpoint, use `Email string` with
`json:"email" validate:"required,email"` in the request type and validate in logic.
Use `json:",default=value"` for configuration defaults.

## Database

Generate an uncached MySQL model from this schema:

<!-- verify: user.sql -->
```sql
CREATE TABLE user (
    id BIGINT NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY email_unique (email)
);
```

```bash
goctl model mysql ddl -src user.sql -dir internal/model --style go_zero
```

Use generated `FindOne(ctx, id)`, `Insert(ctx, &model.User{...})`,
`Update(ctx, &model.User{...})`, and `Delete(ctx, id)`. Put custom queries in the
extension file. With `-cache`, add `cache.CacheConf` to Config and pass it to
`model.NewUserModel(conn, c.Cache)`; the uncached constructor below takes only a connection.

## Config and Service Context

<!-- verify: internal/config/config.go -->
```go
package config

import "github.com/zeromicro/go-zero/rest"

type Config struct {
	rest.RestConf
	MySQL struct {
		DataSource string
	}
	Auth struct {
		AccessSecret string
		AccessExpire int64
	}
}
```

Supply MySQL credentials and a strong JWT secret through your deployment's secret
mechanism. If using environment placeholders in YAML, load with
`conf.UseEnv()` as shown in the entrypoint below.

<!-- verify: etc/user-api.yaml -->
```yaml
Name: user-api
Host: 127.0.0.1
Port: 8888
MySQL:
  DataSource: "${MYSQL_DSN}"
Auth:
  AccessSecret: "${JWT_SECRET}"
  AccessExpire: 3600
```

<!-- verify: internal/svc/service_context.go -->
```go
package svc

import (
	"example.com/user/internal/config"
	"example.com/user/internal/model"

	"github.com/go-playground/validator/v10"
	"github.com/zeromicro/go-zero/core/stores/sqlx"
)

type ServiceContext struct {
	Config    config.Config
	UserModel model.UserModel
	Validator *validator.Validate
}

func NewServiceContext(c config.Config) *ServiceContext {
	conn := sqlx.NewMysql(c.MySQL.DataSource)
	return &ServiceContext{
		Config:    c,
		UserModel: model.NewUserModel(conn),
		Validator: validator.New(),
	}
}
```

## HTTP Errors

`apperror` is a project-local package defined here, not a built-in go-zero API.
Only explicitly public errors expose messages. Unexpected errors are logged with
request context and returned as a generic HTTP 500. For RPC methods use gRPC status
codes instead of this HTTP mapping.
Return a separate response body: go-zero writes values implementing `error` as
plain text, even when their fields have JSON tags.

<!-- verify: internal/apperror/errors.go -->
```go
package apperror

import (
	"context"
	"errors"
	"net/http"

	"github.com/zeromicro/go-zero/core/logc"
)

type Error struct {
	Status  int
	Message string
}

type response struct {
	Message string `json:"message"`
}

func (e *Error) Error() string { return e.Message }

var (
	ErrInvalidInput = &Error{http.StatusBadRequest, "invalid input"}
	ErrUnauthorized = &Error{http.StatusUnauthorized, "unauthorized"}
	ErrForbidden    = &Error{http.StatusForbidden, "forbidden"}
	ErrNotFound     = &Error{http.StatusNotFound, "not found"}
)

func Handler(ctx context.Context, err error) (int, any) {
	var public *Error
	if errors.As(err, &public) && public.Status >= 400 && public.Status < 500 {
		return public.Status, response{Message: public.Message}
	}
	logc.Error(ctx, err)
	return http.StatusInternalServerError, response{Message: "internal error"}
}
```

Register the mapping once at startup, before serving requests:

<!-- verify: user.go -->
```go
package main

import (
	"flag"

	"example.com/user/internal/apperror"
	"example.com/user/internal/config"
	"example.com/user/internal/handler"
	"example.com/user/internal/svc"

	"github.com/zeromicro/go-zero/core/conf"
	"github.com/zeromicro/go-zero/rest"
	"github.com/zeromicro/go-zero/rest/httpx"
)

func main() {
	configFile := flag.String("f", "etc/user-api.yaml", "configuration file")
	flag.Parse()
	var c config.Config
	conf.MustLoad(*configFile, &c, conf.UseEnv())
	httpx.SetErrorHandlerCtx(apperror.Handler)
	server := rest.MustNewServer(c.RestConf)
	defer server.Stop()
	handler.RegisterHandlers(server, svc.NewServiceContext(c))
	server.Start()
}
```

## JWT Claims

The go-zero JWT middleware must verify the token first. This helper validates the
numeric `userId` claim placed in context; it does not verify token signatures.
When issuing tokens, include numeric `userId`, `iat`, and `exp` claims and check
the signing error.

<!-- verify: internal/auth/claims.go -->
```go
package auth

import (
	"context"
	"encoding/json"

	"example.com/user/internal/apperror"
)

func UserID(ctx context.Context) (int64, error) {
	claim, ok := ctx.Value("userId").(json.Number)
	if !ok {
		return 0, apperror.ErrUnauthorized
	}
	id, err := claim.Int64()
	if err != nil || id <= 0 {
		return 0, apperror.ErrUnauthorized
	}
	return id, nil
}
```

## Logic

Use `errors.Is` so wrapped not-found errors are recognized. Return only selected
response fields, and check ownership before querying another user's record.

<!-- verify: internal/logic/user/get_user_logic.go -->
```go
package user

import (
	"context"
	"errors"
	"fmt"

	"example.com/user/internal/apperror"
	"example.com/user/internal/auth"
	"example.com/user/internal/model"
	"example.com/user/internal/svc"
	"example.com/user/internal/types"

	"github.com/zeromicro/go-zero/core/logx"
)

type GetUserLogic struct {
	logx.Logger
	ctx    context.Context
	svcCtx *svc.ServiceContext
}

func NewGetUserLogic(ctx context.Context, svcCtx *svc.ServiceContext) *GetUserLogic {
	return &GetUserLogic{Logger: logx.WithContext(ctx), ctx: ctx, svcCtx: svcCtx}
}

func (l *GetUserLogic) GetUser(req *types.GetUserRequest) (*types.UserResponse, error) {
	if err := l.svcCtx.Validator.StructCtx(l.ctx, req); err != nil {
		return nil, apperror.ErrInvalidInput
	}
	userID, err := auth.UserID(l.ctx)
	if err != nil {
		return nil, err
	}
	if req.Id != userID {
		return nil, apperror.ErrForbidden
	}
	user, err := l.svcCtx.UserModel.FindOne(l.ctx, req.Id)
	if errors.Is(err, model.ErrNotFound) {
		return nil, apperror.ErrNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("find user: %w", err)
	}
	return &types.UserResponse{Id: user.Id, Email: user.Email}, nil
}
```

## Handler

Keep transport parsing in handlers and business checks in logic. Replace the
generated parsing-error branch with a public 400; the generic error mapper above
treats unclassified errors as internal failures.

<!-- verify: internal/handler/user/get_user_handler.go -->
```go
package user

import (
	"net/http"

	"example.com/user/internal/apperror"
	"example.com/user/internal/logic/user"
	"example.com/user/internal/svc"
	"example.com/user/internal/types"

	"github.com/zeromicro/go-zero/rest/httpx"
)

func GetUserHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req types.GetUserRequest
		if err := httpx.Parse(r, &req); err != nil {
			httpx.ErrorCtx(r.Context(), w, apperror.ErrInvalidInput)
			return
		}
		resp, err := user.NewGetUserLogic(r.Context(), svcCtx).GetUser(&req)
		if err != nil {
			httpx.ErrorCtx(r.Context(), w, err)
			return
		}
		httpx.OkJsonCtx(r.Context(), w, resp)
	}
}
```

## Documentation

For each new service, write a README with its purpose, configuration, startup,
testing, and request examples. API.md/RPC.md should document contracts and errors.
For this endpoint, document 400 (invalid ID), 401 (unauthenticated), 403 (another
user's ID), 404 (missing user), and 500 (internal failure). JWT middleware may use a
different response body for rejected tokens; do not promise the application error
envelope for those responses.

```bash
go run user.go -f etc/user-api.yaml
curl -H "Authorization: Bearer $TOKEN" http://localhost:8888/api/users/1
go test ./...
```

Use four backticks around Markdown templates that contain triple-backtick fences,
so copied templates render correctly.
