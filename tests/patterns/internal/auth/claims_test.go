package auth

import (
	"context"
	"encoding/json"
	"errors"
	"testing"

	"example.com/user/internal/apperror"
)

func TestUserID(t *testing.T) {
	for _, tc := range []struct {
		name  string
		claim any
		want  int64
	}{
		{"valid", json.Number("42"), 42},
		{"missing", nil, 0},
		{"string", "42", 0},
		{"float", float64(42), 0},
		{"fraction", json.Number("1.5"), 0},
		{"overflow", json.Number("9223372036854775808"), 0},
		{"zero", json.Number("0"), 0},
		{"negative", json.Number("-1"), 0},
		{"malformed", json.Number("invalid"), 0},
	} {
		t.Run(tc.name, func(t *testing.T) {
			ctx := context.Background()
			if tc.claim != nil {
				ctx = context.WithValue(ctx, "userId", tc.claim)
			}
			got, err := UserID(ctx)
			if got != tc.want {
				t.Fatalf("UserID = %d; want %d", got, tc.want)
			}
			if tc.want == 0 && !errors.Is(err, apperror.ErrUnauthorized) {
				t.Fatalf("expected unauthorized, got %v", err)
			}
			if tc.want != 0 && err != nil {
				t.Fatal(err)
			}
		})
	}
}
