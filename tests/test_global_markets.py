"""Per-country market-cycle phasing must read trend correctly and rank relative strength for rotation."""
import numpy as np
import pandas as pd

from market_traits.global_markets import COUNTRIES, _forward_lean, _metrics, _phase, _valuation_label, global_markets


def _ser(daily_drift, n=400, seed=0, start=100.0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2023-01-01", periods=n)
    steps = rng.normal(daily_drift, 0.008, n)
    return pd.Series(start * np.exp(np.cumsum(steps)), index=idx)


def test_uptrend_is_expansion_side():
    m = _metrics(_ser(0.0015, seed=1))          # steady climb
    assert m["above200"] is True
    assert m["phase"] in ("booming", "expanding")


def test_downtrend_is_recession():
    m = _metrics(_ser(-0.0015, seed=2))         # steady decline
    assert m["above200"] is False
    assert m["phase"] == "recession"


def test_phase_boundaries():
    assert _phase(True, 0.10, 0.05, 0.02, 0.5) == "booming"
    assert _phase(True, 0.10, 0.05, 0.02, 0.1) == "expanding"   # weak efficiency → not booming
    assert _phase(False, -0.10, -0.05, -0.02, 0.3) == "recession"
    assert _phase(False, -0.10, -0.05, 0.05, 0.3) == "recovering"  # turning up


def test_forward_lean_detects_acceleration():
    fast = _forward_lean({"mom6": 0.2, "mom3": 0.05, "mom1": 0.08})   # 1m pace >> prior pace
    slow = _forward_lean({"mom6": 0.2, "mom3": 0.18, "mom1": 0.02})   # decelerating
    assert fast["lean"] == "improving"
    assert slow["lean"] == "deteriorating"


def test_global_markets_ranks_relative_strength():
    """Inject a strong and a weak market → the strong one ranks higher and is phased on the expansion side."""
    etfs = {c[2]: None for c in COUNTRIES}
    etfs["SPY"] = _ser(0.0018, seed=10)         # strong US
    etfs["FXI"] = _ser(-0.0015, seed=11)        # weak China
    g = global_markets(data=etfs)
    us = next(c for c in g["countries"] if c["iso"] == "US")
    cn = next(c for c in g["countries"] if c["iso"] == "CN")
    assert us["rel_strength"] > cn["rel_strength"]
    assert us["phase"] in ("booming", "expanding")
    assert cn["phase"] in ("recession", "recovering", "slowing")
    assert g["countries"] and "note" in g


def test_valuation_label_direction():
    """valuation_pctile: 1.0 = cheapest (lowest PE) among covered markets — a HIGH pctile must read
    'cheap', not 'expensive' (regression: the label thresholds were initially inverted)."""
    assert _valuation_label(0.95) == "cheap"
    assert _valuation_label(0.05) == "expensive"
    assert _valuation_label(0.5) == "mid"


def test_injected_data_carries_seasonality_and_skips_pe_fetch():
    """Injected `data=` (test path) must stay network-free (no pe_ratio fetch) but still compute
    seasonality, which is pure and free (reuses the already-in-memory price series)."""
    etfs = {c[2]: None for c in COUNTRIES}
    etfs["SPY"] = _ser(0.0015, seed=20, n=800)
    g = global_markets(data=etfs)
    us = next(c for c in g["countries"] if c["iso"] == "US")
    assert us["pe_ratio"] is None
    assert "valuation_pctile" not in us            # no PE fetched → nothing to rank
    assert len(us["seasonality"]) == 12
    assert "season_scale" in g and "phases" in g
