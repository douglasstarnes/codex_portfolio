from decimal import Decimal

import httpx

from config import get_settings


class CoinGeckoError(Exception):
    pass


class CoinGeckoConfigError(CoinGeckoError):
    pass


class CoinGeckoPriceNotFoundError(CoinGeckoError):
    pass


class CoinGeckoClient:
    def __init__(self, api_key: str, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def get_current_price_usd(self, coingecko_id: str) -> Decimal:
        prices = self.get_current_prices_usd([coingecko_id])
        return prices[coingecko_id]

    def get_current_prices_usd(self, coingecko_ids: list[str]) -> dict[str, Decimal]:
        if not self.api_key:
            raise CoinGeckoConfigError("CoinGecko API key is not configured")

        unique_ids = list(dict.fromkeys(coingecko_ids))
        if not unique_ids:
            return {}

        try:
            response = httpx.get(
                f"{self.base_url}/simple/price",
                headers={"x-cg-demo-api-key": self.api_key},
                params={"ids": ",".join(unique_ids), "vs_currencies": "usd"},
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise CoinGeckoError("CoinGecko request failed") from exc
        except ValueError as exc:
            raise CoinGeckoError("CoinGecko returned invalid JSON") from exc

        prices: dict[str, Decimal] = {}
        missing_ids: list[str] = []
        for coingecko_id in unique_ids:
            price = data.get(coingecko_id, {}).get("usd")
            if price is None:
                missing_ids.append(coingecko_id)
            else:
                prices[coingecko_id] = Decimal(str(price))

        if missing_ids:
            raise CoinGeckoPriceNotFoundError(
                f"No USD price found for {', '.join(missing_ids)}"
            )

        return prices


def get_coingecko_client() -> CoinGeckoClient:
    settings = get_settings()
    return CoinGeckoClient(
        api_key=settings.coingecko_api_key,
        base_url=settings.coingecko_base_url,
    )
