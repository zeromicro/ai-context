package user

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"example.com/user/internal/apperror"
	"example.com/user/internal/model"
	"example.com/user/internal/svc"

	"github.com/go-playground/validator/v10"
	"github.com/golang-jwt/jwt/v4"
	"github.com/zeromicro/go-zero/rest/handler"
	"github.com/zeromicro/go-zero/rest/httpx"
	"github.com/zeromicro/go-zero/rest/router"
)

type fakeUserModel struct {
	model.UserModel
	err   error
	calls int
	t     *testing.T
}

func (m *fakeUserModel) FindOne(ctx context.Context, id int64) (*model.User, error) {
	m.calls++
	if id != 1 || ctx.Value("userId") != json.Number("1") {
		m.t.Fatal("logic did not pass the authenticated request context and ID")
	}
	if m.err != nil {
		return nil, m.err
	}
	return &model.User{Id: id, Email: "user@example.com"}, nil
}

func TestUserEndpoint(t *testing.T) {
	const secret = "test-only-secret-with-at-least-32-characters"
	token := func(claim any, expiry time.Time, key string) string {
		t.Helper()
		signed, err := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
			"userId": claim, "iat": time.Now().Add(-time.Minute).Unix(), "exp": expiry.Unix(),
		}).SignedString([]byte(key))
		if err != nil {
			t.Fatal(err)
		}
		return signed
	}
	valid := token(1, time.Now().Add(time.Hour), secret)
	httpx.SetErrorHandlerCtx(apperror.Handler)
	t.Cleanup(func() { httpx.SetErrorHandlerCtx(nil) })
	for _, tc := range []struct {
		name, path, token string
		modelErr          error
		status, calls     int
		message           string
	}{
		{"success", "1", valid, nil, 200, 1, ""},
		{"missing token", "1", "", nil, 401, 0, ""},
		{"malformed token", "1", "bad-token", nil, 401, 0, ""},
		{"expired token", "1", token(1, time.Now().Add(-time.Second), secret), nil, 401, 0, ""},
		{"wrong signature", "1", token(1, time.Now().Add(time.Hour), "different-key"), nil, 401, 0, ""},
		{"string claim", "1", token("1", time.Now().Add(time.Hour), secret), nil, 401, 0, "unauthorized"},
		{"invalid path", "abc", valid, nil, 400, 0, "invalid input"},
		{"invalid ID", "0", valid, nil, 400, 0, "invalid input"},
		{"another user", "2", valid, nil, 403, 0, "forbidden"},
		{"not found", "1", valid, model.ErrNotFound, 404, 1, "not found"},
		{"wrapped not found", "1", valid, fmt.Errorf("lookup: %w", model.ErrNotFound), 404, 1, "not found"},
		{"database failure", "1", valid, errors.New("private database details"), 500, 1, "internal error"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			model := &fakeUserModel{err: tc.modelErr, t: t}
			ctx := &svc.ServiceContext{UserModel: model, Validator: validator.New()}
			routes := router.NewRouter()
			protected := handler.Authorize(secret)(GetUserHandler(ctx))
			if err := routes.Handle(http.MethodGet, "/api/users/:id", protected); err != nil {
				t.Fatal(err)
			}
			req := httptest.NewRequest(http.MethodGet, "/api/users/"+tc.path, nil)
			if tc.token != "" {
				req.Header.Set("Authorization", "Bearer "+tc.token)
			}
			response := httptest.NewRecorder()
			routes.ServeHTTP(response, req)
			if response.Code != tc.status {
				t.Fatalf("status = %d; want %d; body = %s", response.Code, tc.status, response.Body)
			}
			if model.calls != tc.calls {
				t.Fatalf("model calls = %d; want %d", model.calls, tc.calls)
			}
			if strings.Contains(response.Body.String(), "private database details") {
				t.Fatal("response exposed internal error details")
			}
			if tc.message != "" {
				var body struct {
					Message string `json:"message"`
				}
				if err := json.Unmarshal(response.Body.Bytes(), &body); err != nil || body.Message != tc.message {
					t.Fatalf("unexpected error body: %s", response.Body)
				}
			}
			if tc.status == 200 {
				var body struct {
					Id    int64  `json:"id"`
					Email string `json:"email"`
				}
				if err := json.Unmarshal(response.Body.Bytes(), &body); err != nil || body.Id != 1 || body.Email != "user@example.com" {
					t.Fatalf("unexpected success body: %s", response.Body)
				}
			}
		})
	}
}
