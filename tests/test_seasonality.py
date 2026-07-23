"""Calendar-month seasonality must find a real month-of-year effect and mark thin history honestly."""
import numpy as np
import pandas as pd

from market_traits.seasonality import monthly_seasonality


def _seasonal_series(years=8, boost_month=12, boost=0.05, seed=0):
    """Daily prices with a fixed drift EXCEPT one calendar month, which gets an extra boost."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2016-01-01", periods=252 * years)
    steps = rng.normal(0.0002, 0.006, len(idx))
    boosted = pd.Series(steps, index=idx)
    boosted[idx.month == boost_month] += boost / 21   # spread the boost over the ~21 trading days
    return pd.Series(100.0 * np.exp(np.cumsum(boosted.to_numpy())), index=idx)


def test_insufficient_history_is_marked_not_computed():
    short = pd.Series(np.linspace(100, 101, 20), index=pd.bdate_range("2024-01-01", periods=20))
    out = monthly_seasonality(short)
    assert len(out) == 12
    assert all(o["band"] == "insufficient" and o["avg_pct"] is None for o in out)


def test_boosted_month_reads_positive():
    px = _seasonal_series(boost_month=12, boost=0.08)
    out = monthly_seasonality(px, min_years=3)
    by_month = {o["month"]: o for o in out}
    dec = by_month[12]
    assert dec["n"] >= 3
    assert dec["avg_pct"] > 0
    assert dec["band"] in ("positive", "strong_positive")


def test_calendar_order_and_shape():
    px = _seasonal_series()
    out = monthly_seasonality(px)
    assert [o["month"] for o in out] == list(range(1, 13))
    assert [o["label"] for o in out][0] == "Jan"
    assert all("color" in o for o in out)
