"""Market weather (DN-208) — is the tape RISK-ON and TRENDING, or choppy/defensive?

The crisis module (DN-200) is the risk-OFF alarm; this is its complement — a regime read that tells you whether the
conditions FAVOUR the strategies we run. Breakout/trend speculation only pays when the market trends (it bleeds in
chop, per the regime split); mean-reversion prefers calm range. So we score five things and turn them into a
"weather" the whole book can gate on: trend, breadth, trending-vs-choppy (Kaufman efficiency), volatility, and
credit risk-appetite. Reports PAST (a daily score history), CURRENT (the regime now), and a FORWARD read (regimes
are sticky — this is a persistence tilt, honestly, not a crash forecast). Free daily data; everything injectable.

`ladder_read()` extends this with a store-of-value read: equities/gold/bonds/housing momentum + volatility
percentiles, an inflation trend (free BLS CPI), and a plain-language "what this means for the horizon ladder"
verdict picked from a decision table (not a single template) — plus per-asset "is this a good window to trade or
hold this" callouts, each backed by a stated percentile threshold. This is explicitly NOT a timing signal: three
independent signal families (price momentum, CPI surprise, HMM regime detection) were tested for switching the
ladder's allocations and all three were rejected (see Market-Analysis repo memory). This function only describes
current conditions for a human to weigh — it never recommends switching assets.
"""
from __future__ import annotations

from typing import Optional

_SECTORS = ["XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLC"]
_LADDER_ASSETS = {"equities": "SPY", "gold": "GLD", "bonds": "TLT", "crypto": "BTC-USD"}
# BTC halving-cycle bottom-timing calibration (Market-Analysis repo memory: btc-halving-cycle-bottom-watch,
# 2026-08-13). Top-anchored, real-time-detectable drawdown trigger -> bottom lag, calibrated off the two
# fully data-verified cycles (2017, 2021 tops; 2013 predates free daily history). n=2 — descriptive watch-item
# only, same as every other ladder read here, never a switching signal.
_BTC_CYCLE_TRIGGERS = {-0.20: (358, 360), -0.30: (350, 346)}
_CPI_SERIES = "CUSR0000SA0"
_HOUSING_SERIES = "CSUSHPINSA"  # Case-Shiller US National Home Price Index, FRED, monthly, ~2mo publication lag


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


def _fred_series(series_id: str, start: str = "2010-01-01") -> dict:
    """Free, keyless FRED CSV export — no API key needed. {date_str: value}, "." (missing) dropped.
    Shells out to curl rather than urllib/requests: this host's Python socket stack reliably stalls reading
    fred.stlouisfed.org's response (a proxy/TLS-stack quirk, not a real network block). Also: sending a spoofed
    User-Agent to this specific endpoint reliably kills the HTTP/2 stream (curl exit 92, INTERNAL_ERROR) — use
    curl's own default UA, unlike the BLS fetch below which needs a UA override to avoid a 403."""
    import subprocess, csv, io
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start}"
    raw = subprocess.run(["curl", "-sf", "--max-time", "20", url],
                         capture_output=True, timeout=25, check=True).stdout.decode()
    out = {}
    for row in list(csv.reader(io.StringIO(raw)))[1:]:
        if len(row) == 2 and row[1] not in (".", ""):
            try:
                out[row[0]] = float(row[1])
            except ValueError:
                continue
    return out


def _bls_series(series_id: str, start_year: int, end_year: int) -> list:
    """Free, keyless BLS v2 API (needs a non-default User-Agent from some hosts, or it 403s). [(date, value)]."""
    import urllib.request, json
    from datetime import date
    out = {}
    y = start_year
    while y <= end_year:
        y2 = min(y + 9, end_year)
        body = json.dumps({"seriesid": [series_id], "startyear": str(y), "endyear": str(y2)}).encode()
        req = urllib.request.Request("https://api.bls.gov/publicAPI/v2/timeseries/data/", data=body,
                                      headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=20).read())
            if d.get("status") == "REQUEST_SUCCEEDED":
                for row in d["Results"]["series"][0]["data"]:
                    if row["period"].startswith("M") and row["period"] != "M13" and row["value"] not in ("-", ""):
                        out[date(int(row["year"]), int(row["period"][1:]), 1)] = float(row["value"])
        except Exception:
            pass
        y = y2 + 1
    return sorted(out.items())


def _pctile(x: float, hist: list) -> float:
    """Rank of x within hist, 0-1. Empty/degenerate history -> 0.5 (neutral, not a claim)."""
    hist = [h for h in hist if h == h]  # drop NaN
    if len(hist) < 20:
        return 0.5
    return sum(1 for h in hist if h <= x) / len(hist)


def asset_snapshot(*, data=None) -> dict:
    """Per-asset momentum + volatility-percentile read for equities/gold/bonds, plus inflation trend and housing.
    All thresholds are percentile-based against the asset's OWN trailing history — never a fixed magic number —
    so "elevated vol" means elevated for THIS asset, not an arbitrary cross-asset cutoff."""
    import statistics
    closes = {}
    if data is not None and "ladder_closes" in data:
        closes = data["ladder_closes"]
    else:
        for name, sym in _LADDER_ASSETS.items():
            try:
                closes[name] = _closes(sym, "2015-01-01")
            except Exception:
                continue

    rows = {}
    for name, s in closes.items():
        s = s.dropna()
        if len(s) < 260:
            continue
        ret = s.pct_change().dropna()
        vol21 = ret.rolling(21).std().dropna()
        cur_vol = float(vol21.iloc[-1]) if len(vol21) else None
        vol_hist = vol21.tail(504).tolist() if len(vol21) else []
        vol_pctile = _pctile(cur_vol, vol_hist) if cur_vol is not None else None
        ma200 = s.rolling(200).mean()
        dist200 = float(s.iloc[-1] / ma200.iloc[-1] - 1) if ma200.iloc[-1] == ma200.iloc[-1] else None
        dist_hist = (s / ma200 - 1).dropna().tail(504).tolist()
        dist_pctile = _pctile(dist200, dist_hist) if dist200 is not None else None
        rows[name] = {
            "last": round(float(s.iloc[-1]), 2),
            "ret_1m_pct": round(float(s.iloc[-1] / s.iloc[-22] - 1) * 100, 2) if len(s) > 22 else None,
            "ret_3m_pct": round(float(s.iloc[-1] / s.iloc[-66] - 1) * 100, 2) if len(s) > 66 else None,
            "ret_12m_pct": round(float(s.iloc[-1] / s.iloc[-252] - 1) * 100, 2) if len(s) > 252 else None,
            "vol_ann_pct": round(cur_vol * (252 ** 0.5) * 100, 2) if cur_vol is not None else None,
            "vol_pctile": round(vol_pctile, 2) if vol_pctile is not None else None,
            "trend_dist_200d_pct": round(dist200 * 100, 2) if dist200 is not None else None,
            "trend_pctile": round(dist_pctile, 2) if dist_pctile is not None else None,
        }

    cpi = {}
    try:
        levels = _bls_series(_CPI_SERIES, 2015, 2027)  # [(date, index_level)]
        yoy = [(d, (v / levels[i - 12][1] - 1) * 100) for i, (d, v) in enumerate(levels) if i >= 12]
        if yoy:
            last_yoy = yoy[-1][1]
            trend3 = yoy[-1][1] - yoy[-4][1] if len(yoy) >= 4 else 0.0
            cpi = {
                "yoy_pct": round(last_yoy, 2),
                "trend_3mo_change_pp": round(trend3, 2),
                "direction": "accelerating" if trend3 > 0.3 else ("cooling" if trend3 < -0.3 else "stable"),
                "as_of": yoy[-1][0].isoformat(),
            }
    except Exception:
        pass

    housing = {}
    try:
        hs = _fred_series(_HOUSING_SERIES, "2015-01-01")
        items = sorted(hs.items())
        if len(items) >= 14:
            last_d, last_v = items[-1]
            yoy_v = next((v for d, v in items if d[:4] == str(int(last_d[:4]) - 1) and d[5:7] == last_d[5:7]), None)
            yoy_pct = (last_v / yoy_v - 1) * 100 if yoy_v else None
            trend3 = items[-1][1] / items[-4][1] - 1 if len(items) >= 4 else None
            housing = {
                "index": round(last_v, 2), "as_of": last_d,
                "yoy_pct": round(yoy_pct, 2) if yoy_pct is not None else None,
                "direction": ("accelerating" if trend3 and trend3 > 0.005 else
                             "cooling" if trend3 and trend3 < -0.005 else "stable") if trend3 is not None else None,
                "note": "Case-Shiller, monthly, ~2mo publication lag — never a tactical/timing instrument, only a "
                        "structural read for the 7yr+ ladder bucket.",
            }
    except Exception:
        pass

    return {"assets": rows, "inflation": cpi, "housing": housing}


_LADDER_STATES = {
    # key -> (verdict: what's happening, action: what to do about it — scoped to calendar-contribution timing
    # and sizing discipline WITHIN the static ladder, never "switch bucket weights", per
    # [[store-of-value-timing-thread-closed]] (3 signal families tested and rejected for that).
    "risk_off": {
        "verdict": ("Risk-off tape. This is the environment the near-term (0-6mo) cash/T-bill bucket exists for — "
                    "capital preservation over any risky-asset bucket right now, regardless of what inflation is doing."),
        "action": ("Hold the line on target weights. Don't add fresh equity/gold exposure ahead of schedule; if a "
                   "scheduled contribution falls in this window, it's fine to let it proceed at target size — "
                   "just don't increase risk-asset weight beyond plan while this persists."),
    },
    "stagflation_signature": {
        "verdict": ("Inflation accelerating, gold volatility elevated, and bonds selling off together — the classic "
                    "stagflation-scare signature. This is exactly the environment the 15% structural gold allocation "
                    "in the 2-7yr and 7yr+ buckets exists for; it's earning its keep as ballast, not something to "
                    "chase or resize."),
        "action": ("No changes. Let the existing gold allocation absorb this — don't add to it beyond target and "
                   "don't sell it for being volatile; both are reacting to a condition it's specifically there for."),
    },
    "benign_growth": {
        "verdict": ("Inflation cooling with a trending risk-on tape and equities not yet stretched — a fairly benign "
                    "setup for the growth-heavy 7yr+ bucket. No asset here is signaling distress; the static "
                    "allocation is doing what it's supposed to without needing a second look."),
        "action": "Proceed with any scheduled contribution at normal target weights — nothing here argues for delaying or front-loading.",
    },
    "equities_stretched": {
        "verdict": ("Equities are trend-extended (top of their own 200d-distance range) — new equity-heavy "
                    "allocations right now are entering at a stretched point in the cycle, not a rich one. Doesn't "
                    "argue for exiting the 7yr+ bucket's equity weight, just for not over-adding beyond target."),
        "action": ("If you're due for a scheduled contribution, still make it at target weight — don't skip it. Just "
                   "don't voluntarily overweight equities beyond plan while they're this extended."),
    },
    "equities_washed_out": {
        "verdict": ("Equities are washed out relative to trend (bottom of their own 200d-distance range) — if you're "
                    "DEPLOYING new money into the 2-7yr/7yr+ buckets on a calendar schedule, this is a relatively "
                    "better entry than a stretched one, though the whole point of a static ladder is not needing to "
                    "time this."),
        "action": ("If a scheduled contribution is due, this is a reasonable window to make it rather than delay — "
                   "still at target weight, not oversized. Don't treat this as a reason to pull FUTURE contributions forward."),
    },
    "gold_hot": {
        "verdict": ("Gold's realized volatility is in the top third of its own 2yr range. Gold in this ladder is held "
                    "structurally as ballast (fixed 15%), not actively traded — elevated vol here is a reason for "
                    "position-sizing discipline if anyone in the household DOES trade gold tactically elsewhere, not a "
                    "reason to touch the static allocation."),
        "action": "No action on the structural allocation. If trading gold tactically outside the ladder, size down given the elevated range.",
    },
    "quiet": {
        "verdict": ("No asset class is showing a stretched or elevated reading right now — a quiet environment where the "
                    "static horizon-ladder allocation needs no attention beyond its normal calendar rebalance."),
        "action": "No action needed. Proceed with the normal calendar rebalance/contribution schedule.",
    },
}


def _ladder_state_key(regime_code: str, cpi: dict, assets: dict) -> str:
    infl_dir = cpi.get("direction", "stable")
    gold = assets.get("gold", {})
    equities = assets.get("equities", {})
    bonds = assets.get("bonds", {})
    gold_hot = (gold.get("vol_pctile") or 0) >= 0.70
    eq_stretched = (equities.get("trend_pctile") or 0.5) >= 0.85
    eq_washed_out = (equities.get("trend_pctile") or 0.5) <= 0.15
    bonds_selling_off = (bonds.get("ret_3m_pct") or 0) < -3

    if regime_code == "risk_off":
        return "risk_off"
    if infl_dir == "accelerating" and gold_hot and bonds_selling_off:
        return "stagflation_signature"
    if infl_dir == "cooling" and regime_code == "risk_on_trending" and not eq_stretched:
        return "benign_growth"
    if eq_stretched:
        return "equities_stretched"
    if eq_washed_out:
        return "equities_washed_out"
    if gold_hot:
        return "gold_hot"
    return "quiet"


def _trade_reads(assets: dict) -> list:
    """Per-asset 'is now a good window to actively trade or add to this' callout — each backed by a stated
    percentile against the asset's OWN trailing 2yr history, not a fixed number. Distinct from `_ladder_verdict`:
    this is asset-by-asset detail, that's the one-paragraph synthesis."""
    out = []
    labels = {"equities": "Equities", "gold": "Gold", "bonds": "Bonds", "crypto": "Crypto (BTC)"}
    for key, label in labels.items():
        a = assets.get(key)
        if not a or a.get("vol_pctile") is None or a.get("trend_pctile") is None:
            continue
        vp, tp = a["vol_pctile"], a["trend_pctile"]
        if vp >= 0.70:
            read = (f"{label}: realized volatility in the top {round((1 - vp) * 100)}% of its own 2yr range — "
                    "better suited to active/tactical trading (bigger moves both ways) than to treating as a "
                    "stable store of value in the near term.")
        elif vp <= 0.20:
            read = (f"{label}: unusually calm — bottom {round(vp * 100)}% of its own 2yr volatility range. Good "
                    "conditions for holding as static ballast; a quiet stretch for active trading (smaller moves "
                    "to trade around).")
        elif tp >= 0.85:
            read = f"{label}: trend-extended relative to its own recent range — not an ideal fresh entry point."
        elif tp <= 0.15:
            read = f"{label}: below its own recent trend range — a relatively better entry than a stretched one."
        else:
            read = f"{label}: trading within its normal range on both trend and volatility — no notable read."
        out.append({"asset": key, "label": label, "vol_pctile": vp, "trend_pctile": tp, "read": read})
    return out


def _btc_cycle_read(*, data=None) -> Optional[dict]:
    """Where BTC sits in its halving-cycle top->bottom drawdown, and the bottom window implied by the
    -20%/-30% trigger->bottom lag calibrated off the 2017 and 2021 cycles (see _BTC_CYCLE_TRIGGERS). n=2 —
    descriptive watch-item, not a signal; same caveat as the rest of this module's ladder reads."""
    import pandas as pd
    from datetime import timedelta

    if data is not None and "ladder_closes" in data and "crypto" in data["ladder_closes"]:
        closes = data["ladder_closes"]["crypto"]
    else:
        try:
            closes = _closes("BTC-USD", "2014-01-01")
        except Exception:
            return None
    closes = closes.dropna()
    if closes.empty:
        return None

    cum_max = closes.cummax()
    drawdown = closes / cum_max - 1
    at_ath = closes >= cum_max
    ath_date = closes.index[at_ath][-1]
    ath_price = float(closes.loc[ath_date])
    cur_price = float(closes.iloc[-1])

    out = {
        "ath_date": str(ath_date)[:10],
        "ath_price": round(ath_price, 2),
        "price": round(cur_price, 2),
        "drawdown_from_ath_pct": round((cur_price / ath_price - 1) * 100, 2),
        "triggers": {},
    }
    since_ath = drawdown.loc[drawdown.index > ath_date]
    for thresh, lags in _BTC_CYCLE_TRIGGERS.items():
        hit = since_ath[since_ath <= thresh]
        if hit.empty:
            out["triggers"][f"{int(thresh * 100)}pct"] = {"triggered": False}
            continue
        trig_date = hit.index[0]
        window_start = trig_date + timedelta(days=min(lags))
        window_end = trig_date + timedelta(days=max(lags))
        out["triggers"][f"{int(thresh * 100)}pct"] = {
            "triggered": True,
            "trigger_date": str(trig_date)[:10],
            "days_since_trigger": int((closes.index[-1] - trig_date).days),
            "historical_lags_days": list(lags),
            "predicted_bottom_window": [str(window_start)[:10], str(window_end)[:10]],
        }
    out["caveat"] = ("n=2 fully-verified cycles (2013's top predates free daily history) — a real, tight-looking "
                      "pattern (2-4 day spread between the two cycles) but not statistically testable at this "
                      "sample size. Descriptive watch-item only, never a switching signal.")
    return out


def ladder_read(*, weather: dict, data=None) -> dict:
    """Combines the existing regime read with the asset-class snapshot into the ladder-facing section."""
    snap = asset_snapshot(data=data)
    state_key = _ladder_state_key(weather.get("regime_code", "mixed"), snap["inflation"], snap["assets"])
    state = _LADDER_STATES[state_key]
    out = {
        "assets": snap["assets"],
        "inflation": snap["inflation"],
        "housing": snap["housing"],
        "ladder_state": state_key,
        "ladder_verdict": state["verdict"],
        "ladder_action": state["action"],
        "trade_reads": _trade_reads(snap["assets"]),
        "caveat": ("Descriptive only — this section reads current conditions; the action line covers "
                   "contribution-timing and sizing discipline WITHIN the static ladder, never switching bucket "
                   "weights. Three independent signal families (price momentum, CPI-surprise, HMM regime "
                   "detection) were tested for timing ladder-bucket switches and all three were rejected."),
    }
    try:
        btc_cycle = _btc_cycle_read(data=data)
        if btc_cycle is not None:
            out["btc_cycle"] = btc_cycle
    except Exception as exc:
        out["btc_cycle"] = {"error": f"btc cycle read unavailable ({str(exc)[:80]})"}
    return out


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
    out = {
        "as_of": dates[-1], "score": cur["score"], "regime": reg["label"], "regime_code": reg["code"],
        "for_book": reg["for_book"],
        "components": {k: cur[k] for k in ("trend", "breadth", "efficiency", "calm", "risk_appetite")},
        "past": {"dates": dates[-252:], "scores": [round(x, 3) for x in hist[-252:]]},
        "forecast": forecast,
        "note": ("Risk-on score = mean of trend, breadth, trending-vs-choppy (Kaufman efficiency), calm (inverse VIX), "
                 "and credit risk-appetite. Complements the crisis gauge. It says which conditions FAVOUR which "
                 "strategies — breakout wants ☀️ trending, mean-reversion/carry prefer 🌀 chop."),
    }
    try:
        out["ladder"] = ladder_read(weather=out, data=data)
    except Exception as exc:
        out["ladder"] = {"error": f"ladder read unavailable ({str(exc)[:80]})"}
    return out
