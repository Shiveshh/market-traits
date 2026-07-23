"""Theme drill-down: subsector/ticker phase reads must reuse the phase engine correctly and stay
network-free when prices are injected (mirrors test_industry_markets.py's pattern)."""
import numpy as np
import pandas as pd

from market_traits.industry_markets import industry_theme_detail


def _ser(daily_drift, n=400, seed=0, start=100.0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2023-01-01", periods=n)
    steps = rng.normal(daily_drift, 0.008, n)
    return pd.Series(start * np.exp(np.cumsum(steps)), index=idx)


def test_unknown_theme_errors():
    assert "error" in industry_theme_detail("not_a_theme", data={})


def test_theme_with_subsectors_ranks_synthetic_baskets():
    """ai_infra has curated subsectors — inject strong Accelerators names and weak Hyperscale names,
    the subsector-level synthetic-basket phase must reflect that split, independent of `overall`
    (which is skipped entirely on the injected-data/test path)."""
    tickers = {
        "NVDA": _ser(0.002, seed=1), "AMD": _ser(0.002, seed=2),          # Accelerators — strong
        "AVGO": _ser(0.002, seed=3), "MRVL": _ser(0.002, seed=4), "ANET": _ser(0.002, seed=5),
        "SMCI": _ser(0.0, seed=6), "DELL": _ser(0.0, seed=7),
        "MSFT": _ser(-0.0015, seed=8), "GOOGL": _ser(-0.0015, seed=9),    # Hyperscale cloud — weak
        "AMZN": _ser(-0.0015, seed=10), "META": _ser(-0.0015, seed=11),
        "VRT": _ser(0.0, seed=12), "ARM": _ser(0.0, seed=13),
        "PLTR": _ser(0.0, seed=14), "PATH": _ser(0.0, seed=15),
    }
    d = industry_theme_detail("ai_infra", data=tickers)
    assert d["key"] == "ai_infra" and d["lifecycle"] == "emerging"
    assert d["overall"] is None                          # network-hitting path skipped when injected
    assert d["tickers"] is None                           # subsectors present → no flat ticker list
    by_name = {s["name"]: s for s in d["subsectors"]}
    assert by_name["Accelerators"]["phase"] in ("booming", "expanding")
    assert by_name["Hyperscale cloud"]["phase"] in ("recession", "recovering", "slowing")
    assert len(by_name["Accelerators"]["ticker_detail"]) == 2


def test_theme_without_subsectors_lists_tickers_flat():
    tickers = {"PANW": _ser(0.001, seed=20), "CRWD": _ser(0.001, seed=21), "ZS": _ser(0.001, seed=22),
               "FTNT": _ser(0.001, seed=23), "S": _ser(0.001, seed=24), "OKTA": _ser(0.001, seed=25),
               "NET": _ser(0.001, seed=26)}
    d = industry_theme_detail("cybersecurity", data=tickers)
    assert d["subsectors"] is None
    assert {t["symbol"] for t in d["tickers"]} == set(tickers)
