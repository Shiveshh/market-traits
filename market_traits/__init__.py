"""market-traits — market/sector/country regime reads (weather, global rotation, industry rotation).

Shared between Market-Analysis and other consuming apps. Everything here is pure/injectable: pass
`data=` to any driver function to run offline (tests, notebooks) with no network calls. Live use pulls
free daily data via yfinance.

Two optional hooks (`pe_fn` on global_markets, `valuation_fn`/`geo_fn` on industry_markets) let a
consumer wire in its own fundamentals/valuation layer; without them those fields are simply omitted.
"""
from market_traits.market_weather import market_weather, weather_series
from market_traits.global_markets import global_markets
from market_traits.industry_markets import industry_markets
from market_traits.seasonality import monthly_seasonality, SEASON_SCALE
from market_traits import tags

__all__ = [
    "market_weather", "weather_series",
    "global_markets", "industry_markets",
    "monthly_seasonality", "SEASON_SCALE",
    "tags",
]
