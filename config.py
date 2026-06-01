from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

load_dotenv()


class ConfigurationError(ValueError):
    """Raised when required application configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    coingecko_api_key: str
    coingecko_base_url: str
    environment: str
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int


def get_settings() -> Settings:
    environment = getenv("ENVIRONMENT", "development")
    jwt_secret_key = getenv("JWT_SECRET_KEY", "")

    if environment.lower() in {"production", "prod"} and not jwt_secret_key:
        raise ConfigurationError(
            "JWT_SECRET_KEY is required when ENVIRONMENT is set to production."
        )

    return Settings(
        coingecko_api_key=getenv("COINGECKO_API_KEY", ""),
        coingecko_base_url=getenv(
            "COINGECKO_BASE_URL",
            "https://api.coingecko.com/api/v3",
        ),
        environment=environment,
        jwt_secret_key=jwt_secret_key,
        jwt_algorithm=getenv("JWT_ALGORITHM", "HS256"),
        jwt_access_token_expire_minutes=int(
            getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        ),
    )
