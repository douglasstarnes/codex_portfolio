import pytest

from config import ConfigurationError, get_settings


def test_get_settings_loads_jwt_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_ALGORITHM", raising=False)
    monkeypatch.delenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)

    settings = get_settings()

    assert settings.environment == "development"
    assert settings.jwt_secret_key == ""
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_access_token_expire_minutes == 30


def test_get_settings_loads_jwt_environment_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS512")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "45")

    settings = get_settings()

    assert settings.jwt_secret_key == "test-secret"
    assert settings.jwt_algorithm == "HS512"
    assert settings.jwt_access_token_expire_minutes == 45


def test_get_settings_requires_jwt_secret_key_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    with pytest.raises(ConfigurationError, match="JWT_SECRET_KEY is required"):
        get_settings()
