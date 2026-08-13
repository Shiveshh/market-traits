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
_SECTOR_NAMES = {
    "XLK": "Technology", "XLF": "Financials", "XLE": "Energy", "XLV": "Health Care",
    "XLY": "Consumer Discretionary", "XLP": "Consumer Staples", "XLI": "Industrials",
    "XLB": "Materials", "XLU": "Utilities", "XLC": "Communication Services",
}
_LADDER_ASSETS = {"equities": "SPY", "gold": "GLD", "bonds": "TLT", "crypto": "BTC-USD"}
# BTC halving-cycle bottom-timing calibration (Market-Analysis repo memory: btc-halving-cycle-bottom-watch,
# 2026-08-13). Top-anchored, real-time-detectable drawdown trigger -> bottom lag, calibrated off the two
# fully data-verified cycles (2017, 2021 tops; 2013 predates free daily history). n=2 — descriptive watch-item
# only, same as every other ladder read here, never a switching signal.
_BTC_CYCLE_TRIGGERS = {-0.20: (358, 360), -0.30: (350, 346)}
_CPI_SERIES = "CUSR0000SA0"
_HOUSING_SERIES = "CSUSHPINSA"  # Case-Shiller US National Home Price Index, FRED, monthly, ~2mo publication lag
_HY_OAS_SERIES = "BAMLH0A0HYM2"  # ICE BofA US High Yield Index Option-Adjusted Spread, FRED, daily
_CLAIMS_SERIES = "ICSA"  # Initial jobless claims, FRED, weekly
_CURVE_SERIES = "T10Y2Y"  # 10y-2y Treasury spread, FRED, daily. Inversion = classic late-cycle warning.
_RECESSION_SERIES = "USREC"  # NBER-based recession indicator, FRED, monthly, 1 = in recession
_UNRATE_SERIES = "UNRATE"  # Unemployment rate, FRED, monthly
_DEBT_GDP_SERIES = "GFDEGDQ188S"  # Federal debt as % of GDP, FRED, quarterly


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


def _fred_daily_series(series_id: str, start: str, idx) -> "pd.Series":
    """FRED series reindexed/ffilled onto `idx` (a price-series DatetimeIndex). Empty series on any fetch failure —
    callers fall back to neutral (0.5) rather than erroring the whole weather read over one flaky source."""
    import pandas as pd
    try:
        raw = _fred_series(series_id, start)
        s = pd.Series(raw)
        s.index = pd.to_datetime(s.index)
        s = s.sort_index()
        return s.reindex(idx, method="ffill")
    except Exception:
        return pd.Series(index=idx, dtype=float)


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
    # Credit spread (HY OAS) and jobs (initial claims): both optional-injectable via `data`; live fetch
    # defaults to FRED when not supplied. Missing/unfetchable -> neutral 0.5 contribution, never a hard error.
    if data is not None and "hy_oas" in data:
        hy_oas = data["hy_oas"].reindex(idx, method="ffill")
    else:
        hy_oas = _fred_daily_series(_HY_OAS_SERIES, start, idx) if data is None else pd.Series(index=idx, dtype=float)
    if data is not None and "claims" in data:
        claims = data["claims"].reindex(idx, method="ffill")
    else:
        claims = _fred_daily_series(_CLAIMS_SERIES, start, idx) if data is None else pd.Series(index=idx, dtype=float)
    claims_mom = claims / claims.shift(20) - 1  # ~4wk-over-4wk change in weekly claims (ffilled onto trading days)
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
        hy_oas_v = hy_oas.loc[d] if d in hy_oas.index else float("nan")
        claims_mom_v = claims_mom.loc[d] if d in claims_mom.index else float("nan")
        comp = {
            "trend": round(trend, 3),
            "breadth": round(float(breadth.loc[d]), 3),
            "efficiency": round(float(er.loc[d]), 3),
            "calm": round(_clip01(-float(vixr.loc[d]), -35, -13), 3),      # low VIX = calm (inverted ramp)
            "risk_appetite": round(_clip01(float(credit_mom.loc[d]) if pd.notna(credit_mom.loc[d]) else 0, -0.02, 0.02), 3),
            # HY OAS spread: empirically (HAC/Newey-West regression on fwd 20d/60d SPY returns, N~700-730,
            # t=2.45/3.86) a WIDER spread has led higher forward returns over this series' available free
            # history, not tighter — likely mean-reversion-after-stress rather than a stable structural
            # lead/lag, and the free keyless FRED pull for this series only covers ~2yr (source truncates
            # regardless of requested start date) so this reading is a single-regime sample, not confirmed
            # across a full cycle. Oriented to match the measured (not assumed) direction; revisit if a
            # longer history becomes available to re-test.
            "credit_spread": round(_clip01(float(hy_oas_v), 3.0, 8.0) if pd.notna(hy_oas_v) else 0.5, 3),
            # Initial claims: empirically (same method, N~3600+, t=3.96/9.60) RISING claims momentum has
            # led higher forward SPY returns, not falling — claims are a lagging/late-cycle indicator and
            # the market tends to rally into the labour-market trough ("bad news is good news" / easing
            # expectations). Oriented to match the measured direction rather than the naive "healthy jobs
            # = risk-on" assumption, which tested backwards.
            "jobs": round(_clip01(float(claims_mom_v), -0.15, 0.10) if pd.notna(claims_mom_v) else 0.5, 3),
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


def sector_breakdown(*, data=None) -> dict:
    """Per-sector detail behind the aggregate `breadth` score component: price vs its own 200d MA, 1m/3m return,
    and relative strength vs SPY over the same window. `breadth` only reports the fraction above trend; this is
    the same 10 SPDR sectors broken out individually (XLI/XLY included) so a reader can see which sectors are
    driving that number rather than just the aggregate."""
    import pandas as pd
    if data is not None and "sectors" in data and "spy" in data:
        spy, sectors = data["spy"], data["sectors"]
    else:
        spy = _closes("SPY", "2018-01-01")
        sectors = {s: _closes(s, "2018-01-01") for s in _SECTORS}

    spy_ret_3m = float(spy.iloc[-1] / spy.iloc[-66] - 1) if len(spy) > 66 else None
    rows = []
    for sym, s in sectors.items():
        s = s.dropna()
        if len(s) < 22:
            continue
        ma200 = s.rolling(200).mean()
        above_200d = bool(s.iloc[-1] > ma200.iloc[-1]) if pd.notna(ma200.iloc[-1]) else None
        ret_1m = float(s.iloc[-1] / s.iloc[-22] - 1) * 100 if len(s) > 22 else None
        ret_3m = float(s.iloc[-1] / s.iloc[-66] - 1) * 100 if len(s) > 66 else None
        rel_strength_3m = (ret_3m / 100 - spy_ret_3m) * 100 if ret_3m is not None and spy_ret_3m is not None else None
        rows.append({
            "symbol": sym,
            "name": _SECTOR_NAMES.get(sym, sym),
            "last": round(float(s.iloc[-1]), 2),
            "above_200d_ma": above_200d,
            "ret_1m_pct": round(ret_1m, 2) if ret_1m is not None else None,
            "ret_3m_pct": round(ret_3m, 2) if ret_3m is not None else None,
            "rel_strength_vs_spy_3m_pct": round(rel_strength_3m, 2) if rel_strength_3m is not None else None,
        })
    rows.sort(key=lambda r: (r["ret_3m_pct"] is None, -(r["ret_3m_pct"] or 0)))
    return {"sectors": rows, "as_of": str(spy.index[-1])[:10] if len(spy) else None}


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


_DEBT_CYCLE_STAGES = {
    # Dalio's short-term debt cycle, collapsed to 4 stages a monthly rule can classify from free FRED data.
    # code -> (label, what's happening, investing guidance FOR THIS STAGE — sizing/tilt within the existing
    # static horizon ladder, never a call to abandon it; see store-of-value-timing-thread-closed).
    "bust_deleveraging": {
        "label": "Bust / deleveraging",
        "what": ("NBER-recession conditions: credit contracting, growth negative, the leverage built up in the "
                 "prior boom stage unwinding. This is the stage the Fed/gov CAN soften (rate cuts, QE, fiscal "
                 "transfers) but can't skip — every prior soft landing pushed the leverage further into the "
                 "system rather than removing it, which is why the cycle keeps recurring."),
        "invest": ("Capital preservation first — this is what the 0-6mo cash/T-bill bucket exists for. Once "
                   "spreads/equities are visibly washed out (not just down), this is historically the highest "
                   "risk-adjusted window to deploy dry powder into the 2-7yr/7yr+ equity sleeves at target "
                   "weight — not overweight, just don't skip a scheduled contribution here. Avoid selling gold "
                   "or long bonds into the panic; they're the ballast this stage is for."),
    },
    "early_cycle": {
        "label": "Early-cycle recovery",
        "what": ("Within ~18 months of the last recession's end. Credit is still cautious, valuations reset, "
                 "the yield curve is typically steep (short rates cut hard, long rates anchored) — the healthiest "
                 "part of the cycle to be adding risk, because leverage hasn't rebuilt yet."),
        "invest": ("Good environment to be at or slightly ahead of target equity weight if a scheduled "
                   "contribution is due; the asymmetry favors being early here over waiting for confirmation. "
                   "Gold/TIPS sleeve stays at target — it's not this stage's job to earn its keep, the next one is."),
    },
    "mid_cycle": {
        "label": "Mid-cycle expansion",
        "what": ("Growth expanding, curve still positively sloped, no acute stress signature. The unremarkable "
                 "middle of the cycle — leverage is building but hasn't reached the point where the curve or "
                 "credit market is flagging it yet."),
        "invest": ("Nothing to do — proceed at normal target weights on the normal calendar schedule. This is "
                   "the stage the static ladder is designed to be boring in."),
    },
    "late_cycle_boom": {
        "label": "Late-cycle boom",
        "what": ("The yield curve has inverted (or credit spreads are at multi-year tights while debt/GDP keeps "
                 "climbing) — the classic pre-recession leverage-and-euphoria signature. Historically this is "
                 "where the deferral mechanism (rate cuts avoiding the LAST slowdown) is most visible: debt has "
                 "kept compounding on top of debt rather than being paid down, and short rates are now high "
                 "enough to start choking it off."),
        "invest": ("Don't chase — proceed with scheduled contributions at target weight, not overweight. This is "
                   "the stage to make sure the 0-6mo cash bucket is actually topped up to target (not drifted "
                   "down from spending risk assets' gains) so there's real dry powder when the bust stage "
                   "arrives, and to lean on the gold/TIPS sleeve as the stagflation/confidence hedge rather than "
                   "trimming it for looking like dead weight in a rising market."),
    },
}


def _classify_debt_cycle(dates, curve, recession, unrate, debt_gdp_yoy, hy_oas_pctile) -> list:
    """Rule-based monthly stage assignment. Returns list of stage codes aligned to `dates`."""
    stages = []
    months_since_recession = None
    for i, d in enumerate(dates):
        rec = recession[i]
        if rec == 1:
            stages.append("bust_deleveraging")
            months_since_recession = 0
            continue
        if months_since_recession is not None:
            months_since_recession += 1
        if months_since_recession is not None and months_since_recession <= 18:
            stages.append("early_cycle")
            continue
        c = curve[i]
        dg = debt_gdp_yoy[i] if i < len(debt_gdp_yoy) else None
        hy = hy_oas_pctile[i] if i < len(hy_oas_pctile) else None
        late_signature = (c is not None and c == c and c < 0) or (
            dg is not None and dg == dg and dg > 3.0 and hy is not None and hy == hy and hy <= 0.25
        )
        stages.append("late_cycle_boom" if late_signature else "mid_cycle")
    return stages


def debt_cycle_read(*, start: str = "1990-01-01", data=None) -> dict:
    """Dalio-style boom/bust (short-term debt cycle) read: monthly stage history for the graph, plus current
    stage / what preceded it / plain-language investing guidance for that stage — all scoped to sizing/tilt
    WITHIN the existing static horizon ladder (see store-of-value-timing-thread-closed), never a call to switch
    bucket weights or time an exit. Free FRED data only: 10y-2y curve, NBER recession flag, unemployment, HY OAS
    (reused from weather_series), and Federal debt/GDP."""
    import pandas as pd

    if data is not None and "debt_cycle_raw" in data:
        curve_raw, rec_raw, unrate_raw, debt_raw, hy_raw = data["debt_cycle_raw"]
    else:
        curve_raw = _fred_series(_CURVE_SERIES, start)
        rec_raw = _fred_series(_RECESSION_SERIES, start)
        unrate_raw = _fred_series(_UNRATE_SERIES, start)
        debt_raw = _fred_series(_DEBT_GDP_SERIES, "1985-01-01")
        hy_raw = _fred_series(_HY_OAS_SERIES, start)

    def _monthly(raw: dict) -> "pd.Series":
        s = pd.Series(raw)
        s.index = pd.to_datetime(s.index)
        return s.sort_index().resample("MS").last()

    curve_m = _monthly(curve_raw)
    rec_m = _monthly(rec_raw)
    unrate_m = _monthly(unrate_raw)
    debt_m = _monthly(debt_raw).reindex(curve_m.index, method="ffill")
    hy_m = _monthly(hy_raw)

    idx = curve_m.index.intersection(rec_m.index).intersection(unrate_m.index)
    idx = idx[idx >= pd.Timestamp(start)]
    if len(idx) < 24:
        return {"error": "insufficient FRED history for debt-cycle read"}

    curve = curve_m.reindex(idx)
    rec = rec_m.reindex(idx)
    unrate = unrate_m.reindex(idx)
    debt = debt_m.reindex(idx)
    debt_yoy = (debt / debt.shift(12) - 1) * 100
    hy = hy_m.reindex(idx, method="ffill")
    hy_pctile = hy.rolling(60, min_periods=20).apply(lambda w: (w <= w.iloc[-1]).mean(), raw=False)

    dates = [str(d)[:10] for d in idx]
    stages = _classify_debt_cycle(
        dates, curve.tolist(), rec.tolist(), unrate.tolist(), debt_yoy.tolist(), hy_pctile.tolist()
    )
    stage_code = {"bust_deleveraging": 4, "early_cycle": 1, "mid_cycle": 2, "late_cycle_boom": 3}
    numeric = [stage_code[s] for s in stages]

    cur = stages[-1]
    # find the prior distinct stage and how long the current one has held
    months_in_stage = 1
    for s in reversed(stages[:-1]):
        if s == cur:
            months_in_stage += 1
        else:
            break
    prior_stage = None
    for s in reversed(stages[: len(stages) - months_in_stage]):
        if s != cur:
            prior_stage = s
            break

    info = _DEBT_CYCLE_STAGES[cur]
    prior_label = _DEBT_CYCLE_STAGES[prior_stage]["label"] if prior_stage else None
    verdict = (
        f"**Where we are:** {info['label']} — in this stage for {months_in_stage} month"
        f"{'s' if months_in_stage != 1 else ''} so far. {info['what']}"
    )
    if prior_label:
        verdict += f" **What came before:** the prior stage was {prior_label}."
    next_read = {
        "bust_deleveraging": "Base rate: this resolves into an early-cycle recovery, though the timing is not forecastable.",
        "early_cycle": "Base rate: transitions into mid-cycle expansion as the recovery matures — no signal times this, it's a persistence read.",
        "mid_cycle": "Base rate: continues until either a late-cycle warning signature (curve inversion) appears or a recession hits directly — both are monitored here, neither is predicted in advance.",
        "late_cycle_boom": "Base rate: this stage has historically preceded a recession by a few quarters to ~2 years — a warning window, not a countdown.",
    }
    verdict += f" **What's next:** {next_read[cur]}"

    return {
        "history": {"dates": dates, "stage_code": numeric, "stage_label": stages,
                     "recession_flag": [int(r) if r == r else 0 for r in rec.tolist()]},
        "current_stage": cur,
        "current_stage_label": info["label"],
        "months_in_stage": months_in_stage,
        "prior_stage": prior_stage,
        "prior_stage_label": prior_label,
        "verdict": verdict,
        "investing_guidance": info["invest"],
        "components": {
            "curve_10y2y": round(float(curve.iloc[-1]), 3) if curve.iloc[-1] == curve.iloc[-1] else None,
            "unemployment_pct": round(float(unrate.iloc[-1]), 2) if unrate.iloc[-1] == unrate.iloc[-1] else None,
            "debt_gdp_yoy_pp": round(float(debt_yoy.iloc[-1]), 2) if debt_yoy.iloc[-1] == debt_yoy.iloc[-1] else None,
            "hy_oas_pctile_5y": round(float(hy_pctile.iloc[-1]), 2) if hy_pctile.iloc[-1] == hy_pctile.iloc[-1] else None,
        },
        "caveat": ("Descriptive stage classification from free macro data (10y-2y curve, NBER recession flag, "
                   "unemployment, Federal debt/GDP, HY credit spreads) — a base-rate/persistence read, not a "
                   "timing signal. The 'what's next' line states historical tendency, never a forecast date. "
                   "Guidance is scoped to sizing/tilt discipline WITHIN the existing static ladder; three "
                   "independent signal families were already tested and rejected for actively timing ladder "
                   "switches (store-of-value-timing-thread-closed)."),
    }


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
        "components": {k: cur[k] for k in
                       ("trend", "breadth", "efficiency", "calm", "risk_appetite", "credit_spread", "jobs")},
        "past": {"dates": dates[-252:], "scores": [round(x, 3) for x in hist[-252:]]},
        "forecast": forecast,
        "note": ("Risk-on score = mean of trend, breadth, trending-vs-choppy (Kaufman efficiency), calm (inverse "
                 "VIX), credit risk-appetite (HYG/LQD momentum), credit spread level (HY OAS — empirically wider "
                 "spread has led higher forward returns over this series' short free history, so scored as such, "
                 "not the naive tighter=risk-on assumption), and jobs (initial-claims momentum — empirically "
                 "rising claims has led higher forward returns, consistent with claims being a lagging indicator "
                 "and markets rallying into the labour-market trough, so scored opposite the naive healthy-jobs "
                 "assumption). Complements the crisis gauge. It says which conditions FAVOUR which strategies — "
                 "breakout wants ☀️ trending, mean-reversion/carry prefer 🌀 chop."),
    }
    try:
        out["sectors"] = sector_breakdown(data=data)
    except Exception as exc:
        out["sectors"] = {"error": f"sector breakdown unavailable ({str(exc)[:80]})"}
    try:
        out["ladder"] = ladder_read(weather=out, data=data)
    except Exception as exc:
        out["ladder"] = {"error": f"ladder read unavailable ({str(exc)[:80]})"}
    try:
        out["debt_cycle"] = debt_cycle_read(data=data)
    except Exception as exc:
        out["debt_cycle"] = {"error": f"debt-cycle read unavailable ({str(exc)[:80]})"}
    return out
