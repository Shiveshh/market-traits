# market-traits

Market/sector/country regime reads, extracted from the Market-Analysis "Market Traits" page so it can
be shared across repos:

- `market_weather` — is the tape risk-on and trending, or choppy/defensive? (trend, breadth,
  trending-vs-choppy efficiency, volatility, credit risk-appetite → one score + regime label)
- `global_markets` — per-country business-cycle phase (booming/expanding/slowing/recession/recovering)
  from ~49 free country-ETF proxies, with relative-strength rotation ranking
- `industry_markets` — the sector/theme-level twin of `global_markets`, over ~19 curated secular themes
  (AI infra, semiconductors, nuclear, etc.)
- `tags` — the curated ticker → sector-theme map that `industry_markets` groups by
- `seasonality` — calendar-month average-return seasonality, reused by both rotation maps

## Design

Everything is pure/injectable — pass `data=` (a dict of pre-fetched price series) to any driver
function and it runs with zero network calls, which is how the test suite exercises it. Live callers
omit `data` and it pulls free daily data via `yfinance`.

`global_markets()` and `industry_markets()` each have one or two optional hook parameters
(`pe_fn`, `valuation_fn`, `geo_fn`) for a consumer to wire in its own fundamentals/valuation layer
(e.g. a factor-screen engine). Without them, those specific fields are simply omitted — this package
has no opinion on how you compute fair value.

## Install

From a consuming repo:

```
pip install -e /path/to/market-traits          # local dev, editable
# or, once pushed to a remote:
pip install git+https://github.com/Shiveshh/market-traits.git
```

## Usage

```python
from market_traits import market_weather, global_markets, industry_markets

market_weather()      # {"score", "regime", "regime_code", "components", "past", "forecast", ...}
global_markets()      # {"countries", "phases", "leaders", "laggards", ...}
industry_markets()    # {"industries", "phases", "leaders", "laggards", ...}
```

## Keeping two+ consuming repos in sync

Edit here, commit, push. Each consuming repo picks up the change with:

```
pip install -U git+https://github.com/Shiveshh/market-traits.git
```

or pin an exact commit/tag in `requirements.txt` for reproducible builds, bumping it deliberately.
