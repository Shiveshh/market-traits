"""Country drill-down: sub-market phase reads must reuse the phase engine correctly and stay
network-free when prices are injected (mirrors test_global_markets.py's pattern)."""
import numpy as np
import pandas as pd

from market_traits.global_markets import country_submarket_detail


def _ser(daily_drift, n=400, seed=0, start=100.0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2023-01-01", periods=n)
    steps = rng.normal(daily_drift, 0.008, n)
    return pd.Series(start * np.exp(np.cumsum(steps)), index=idx)


def test_unknown_country_errors():
    assert "error" in country_submarket_detail("ZZ", data={})


def test_country_with_no_submarkets_returns_empty_list():
    d = country_submarket_detail("DE", data={})   # Germany has no curated sub-markets
    assert d["sub_markets"] == []
    assert d["overall"] is None                   # network-hitting path skipped when injected


def test_country_with_submarkets_ranks_them():
    """US has three curated sub-markets — inject a strong Nasdaq proxy and a weak Russell proxy,
    the sub-market phase read must reflect that split."""
    etfs = {"QQQ": _ser(0.002, seed=1), "DIA": _ser(0.0, seed=2), "IWM": _ser(-0.0015, seed=3)}
    d = country_submarket_detail("US", data=etfs)
    by_etf = {s["etf"]: s for s in d["sub_markets"]}
    assert by_etf["QQQ"]["phase"] in ("booming", "expanding")
    assert by_etf["IWM"]["phase"] in ("recession", "recovering", "slowing")
    assert len(by_etf["QQQ"]["seasonality"]) == 12
