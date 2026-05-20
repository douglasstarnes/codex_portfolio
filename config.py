from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    coingecko_api_key: str
    coingecko_base_url: str


def get_settings() -> Settings:
    return Settings(
        coingecko_api_key=getenv("COINGECKO_API_KEY", ""),
        coingecko_base_url=getenv(
            "COINGECKO_BASE_URL",
            "https://api.coingecko.com/api/v3",
        ),
    )
