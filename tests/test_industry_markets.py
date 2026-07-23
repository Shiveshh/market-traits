"""Industry rotation map must reuse global_markets.py's phase logic correctly per theme and stay
network-free when prices are injected (mirrors test_global_markets.py's pattern)."""
import numpy as np
import pandas as pd

from market_traits.industry_markets import REPRESENTATIVE_ETF, industry_markets


def _ser(daily_drift, n=400, seed=0, start=100.0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2023-01-01", periods=n)
    steps = rng.normal(daily_drift, 0.008, n)
    return pd.Series(start * np.exp(np.cumsum(steps)), index=idx)


def test_industry_markets_shape_and_no_network_on_injected_data():
    etfs = {e: None for e in set(REPRESENTATIVE_ETF.values())}
    etfs["SMH"] = _ser(0.0018, seed=1)   # strong semiconductors
    etfs["XBI"] = _ser(-0.0015, seed=2)  # weak biotech tools
    g = industry_markets(data=etfs)

    assert g["industries"] and "note" in g
    assert "phases" in g and "season_scale" in g

    semis = next(r for r in g["industries"] if r["key"] == "semiconductors")
    biotech = next(r for r in g["industries"] if r["key"] == "biotech_tools")
    assert semis["rel_strength"] > biotech["rel_strength"]
    assert semis["phase"] in ("booming", "expanding")
    assert biotech["phase"] in ("recession", "recovering", "slowing")
    assert len(semis["seasonality"]) == 12
    # injected data path skips valuation_fn/geo_fn even if the caller passed them (see module docstring)
    assert semis["geography"] == []
    assert semis["valuation"] == {"n": 0, "verdict": "insufficient_data"}


def test_unknown_theme_when_etf_missing():
    g = industry_markets(data={e: None for e in set(REPRESENTATIVE_ETF.values())})
    assert all(r["phase"] == "unknown" for r in g["industries"])
    assert all("rel_strength" not in r for r in g["industries"])
