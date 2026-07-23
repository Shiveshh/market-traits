"""Market weather regime read: shape + score bounds."""
import numpy as np
import pandas as pd
from market_traits.market_weather import market_weather


def _series(T=900, drift=0.0004, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2020-01-01", periods=T)
    return pd.Series(100 * np.exp(np.cumsum(rng.normal(drift, 0.01, T))), index=idx)


def test_weather_shape():
    spy = _series(); vix = pd.Series(18.0, index=spy.index)
    data = {"spy": spy, "vix": vix, "hyg": _series(seed=1), "lqd": _series(seed=2),
            "sectors": {f"X{i}": _series(seed=i + 3) for i in range(4)}}
    w = market_weather(data=data)
    assert "regime" in w and 0 <= w["score"] <= 1
    assert w["past"]["scores"] and "efficiency" in w["components"]
