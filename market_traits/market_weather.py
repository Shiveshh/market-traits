"""Market weather (DN-208) — is the tape RISK-ON and TRENDING, or choppy/defensive?

The crisis module (DN-200) is the risk-OFF alarm; this is its complement — a regime read that tells you whether the
conditions FAVOUR the strategies we run. Breakout/trend speculation only pays when the market trends (it bleeds in
chop, per the regime split); mean-reversion prefers calm range. So we score five things and turn them into a
"weather" the whole book can gate on: trend, breadth, trending-vs-choppy (Kaufman efficiency), volatility, and
credit risk-appetite. Reports PAST (a daily score history), CURRENT (the regime now), and a FORWARD read (regimes
are sticky — this is a persistence tilt, honestly, not a crash forecast). Free daily data; everything injectable.
"""
from __future__ import annotations

from typing import Optional

_SECTORS = ["XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLC"]


def _closes(sym, start):
    import yfinance as yf
    import pandas as pd
    df = yf.download(sym, start=start, interval="1d", auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df["Close"].dropna()


def _efficiency_ratio(s, n=20):
    """Kaufman efficiency ratio: |net move over n| / sum|daily moves|. →1 = clean trend, →0 = choppy."""
    net = (s - s.shift(n)).abs()
    vol = s.diff().abs().rolling(n).sum()
    return (net / vol).clip(0, 1)


def _clip01(x, a, b):
    return float(max(0.0, min(1.0, (x - a) / (b - a)))) if b != a else 0.0


def weather_series(*, start: str = "2018-01-01", data=None) -> dict:
    """Compute the daily risk-on score + its components over the window (for PAST timeline + CURRENT)."""
    import pandas as pd
    if data is None:
        spy = _closes("SPY", start); vix = _closes("^VIX", start)
        hyg = _closes("HYG", start); lqd = _closes("LQD", start)
        sectors = {s: _closes(s, start) for s in _SECTORS}
    else:
        spy, vix, hyg, lqd, sectors = data["spy"], data["vix"], data["hyg"], data["lqd"], data["sectors"]
    idx = spy.index
    ma200 = spy.rolling(200).mean()
    er = _efficiency_ratio(spy, 20)
    # breadth: fraction of sectors above their own 200d MA
    breadth = pd.Series(0.0, index=idx)
    aligned = []
    for s, ser in sectors.items():
        r = ser.reindex(idx).ffill()
        aligned.append((r > r.rolling(200).mean()).astype(float))
    if aligned:
        breadth = sum(aligned) / len(aligned)
    hl = (hyg.reindex(idx).ffill() / lqd.reindex(idx).ffill())
    credit_mom = hl / hl.shift(20) - 1
    vixr = vix.reindex(idx).ffill()

    rows = {}
    for d in idx:
        if pd.isna(ma200.loc[d]) or pd.isna(er.loc[d]):
            continue
        trend = 1.0 if spy.loc[d] > ma200.loc[d] else 0.0
        trend = 0.5 * trend + 0.5 * _clip01(float(spy.loc[d] / ma200.loc[d]), 0.95, 1.08)
        comp = {
            "trend": round(trend, 3),
            "breadth": round(float(breadth.loc[d]), 3),
            "efficiency": round(float(er.loc[d]), 3),
            "calm": round(_clip01(-float(vixr.loc[d]), -35, -13), 3),      # low VIX = calm (inverted ramp)
            "risk_appetite": round(_clip01(float(credit_mom.loc[d]) if pd.notna(credit_mom.loc[d]) else 0, -0.02, 0.02), 3),
        }
        rows[str(d)[:10]] = {"score": round(sum(comp.values()) / len(comp), 3), **comp}
    return {"series": rows, "dates": list(rows.keys())}


def _regime(score, comp) -> dict:
    # `code` is the STRUCTURED key downstream gates should use (never the emoji label — that's for display).
    er = comp["efficiency"]
    trending = er >= 0.30
    if score >= 0.60 and comp["trend"] >= 0.6 and trending:
        return {"code": "risk_on_trending", "label": "☀️ Risk-on · trending up",
                "for_book": "breakout/momentum LONG favoured; mean-reversion weaker"}
    if score <= 0.35:
        return {"code": "risk_off", "label": "🌧️ Risk-off · defensive",
                "for_book": "trend SHORTS + de-risk; cut long exposure"}
    if not trending:
        return {"code": "choppy", "label": "🌀 Choppy · rangebound",
                "for_book": "breakout bleeds (whipsaws) — mean-reversion/carry favoured"}
    return {"code": "mixed", "label": "⛅ Mixed · transitioning",
            "for_book": "size down directional bets; wait for the trend to set"}


_CACHE: dict = {"t": 0.0, "val": None}


def market_weather(*, start: str = "2018-01-01", data=None, ttl: int = 1800) -> dict:
    """Whole picture: CURRENT regime, PAST score timeline, and a FORWARD persistence read.
    Cached for `ttl` seconds — the endpoint is heavy (pulls ~8y × 14 symbols), so don't re-pull on every page load."""
    import time
    if data is None and _CACHE["val"] is not None and (time.time() - _CACHE["t"]) < ttl:
        return _CACHE["val"]
    out = _compute_weather(start=start, data=data)
    if data is None and "error" not in out:
        _CACHE.update(t=time.time(), val=out)
    return out


def _compute_weather(*, start: str = "2018-01-01", data=None) -> dict:
    ws = weather_series(start=start, data=data)
    dates = ws["dates"]
    if not dates:
        return {"error": "no data"}
    cur = ws["series"][dates[-1]]
    reg = _regime(cur["score"], cur)
    hist = [ws["series"][d]["score"] for d in dates]
    # forward read: regimes persist. Momentum of the score over 20d + how long the current regime has held.
    slope = round(cur["score"] - ws["series"][dates[-21]]["score"], 3) if len(dates) > 21 else 0.0
    drift = "improving" if slope > 0.05 else ("deteriorating" if slope < -0.05 else "stable")
    forecast = {
        "read": f"{reg['label'].split(' ')[0]} likely to persist ({drift})",
        "score_20d_change": slope,
        "confidence": "regimes are sticky, so near-term persistence is the base rate — NOT a crash/rally forecast",
    }
    return {
        "as_of": dates[-1], "score": cur["score"], "regime": reg["label"], "regime_code": reg["code"],
        "for_book": reg["for_book"],
        "components": {k: cur[k] for k in ("trend", "breadth", "efficiency", "calm", "risk_appetite")},
        "past": {"dates": dates[-252:], "scores": [round(x, 3) for x in hist[-252:]]},
        "forecast": forecast,
        "note": ("Risk-on score = mean of trend, breadth, trending-vs-choppy (Kaufman efficiency), calm (inverse VIX), "
                 "and credit risk-appetite. Complements the crisis gauge. It says which conditions FAVOUR which "
                 "strategies — breakout wants ☀️ trending, mean-reversion/carry prefer 🌀 chop."),
    }
