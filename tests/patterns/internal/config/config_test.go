package config

import (
	"testing"

	"github.com/zeromicro/go-zero/core/conf"
)

func TestDocumentedConfig(t *testing.T) {
	const dsn = "example:password@tcp(localhost:3306)/users"
	const secret = "test-only-jwt-secret-at-least-32-characters"
	t.Setenv("MYSQL_DSN", dsn)
	t.Setenv("JWT_SECRET", secret)
	var c Config
	if err := conf.Load("../../etc/user-api.yaml", &c, conf.UseEnv()); err != nil {
		t.Fatal(err)
	}
	if c.MySQL.DataSource != dsn || c.Auth.AccessSecret != secret {
		t.Fatal("documented environment placeholders were not expanded")
	}
	if c.Name != "user-api" || c.Host != "127.0.0.1" || c.Port != 8888 || c.Auth.AccessExpire != 3600 {
		t.Fatalf("unexpected service configuration: name=%s host=%s port=%d expiry=%d",
			c.Name, c.Host, c.Port, c.Auth.AccessExpire)
	}
}
