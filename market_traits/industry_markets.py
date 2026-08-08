"""Industry rotation map — the sector/theme-level twin of global_markets.py.

Same macro thesis, applied to secular themes instead of countries: read a basket of proxy ETFs (one
per theme, from tags.py's THEME_ETFS) and place each theme into a market-cycle PHASE using the exact
same trend/momentum signals (price vs 200d, 6/3/1-month momentum, Kaufman efficiency) — reused
directly from global_markets.py, not reimplemented. Reports CURRENT phase, PAST monthly phase
history, FORWARD lean, calendar-month seasonality (also reused).

Themes span both directions of secular change: "emerging" (AI infra, nuclear, ...) and "fading"
(legacy retail, ICE autos, fossil-fuel majors, linear media) — see tags.THEME_LIFECYCLE. Same phase
math either way; lifecycle is just a label for which side of the disruption a theme sits on.

Two things a consumer app usually wants layered in but that this package doesn't own:
  - a fair-value-based valuation verdict per theme (needs a fundamentals/factor-screen engine)
  - a "where it lives" geographic breakdown from each theme's constituent tickers' HQ country
Pass `valuation_fn(groups) -> [{"key", "n", "verdict", ...}]` and/or `geo_fn(tickers) -> [{"country", "n"}]`
to wire those in; without them the fields are simply omitted/empty, same "everything injectable"
convention as market_weather.py and global_markets.py.
"""
from __future__ import annotations

from typing import Callable, Optional

from market_traits.global_markets import (
    PHASES,
    _download,
    _forward_lean,
    _metrics,
    _past_phases,
)
from market_traits.seasonality import SEASON_SCALE, monthly_seasonality
from market_traits.tags import THEME_DESCRIPTIONS, THEME_LABELS, subsectors_for, theme_groups

# theme key → the single most liquid/representative proxy ETF (deliberately curated, not just
# "first alphabetically" out of THEME_ETFS, which lists every reasonable proxy per theme).
REPRESENTATIVE_ETF: dict[str, str] = {
    "ai_infra": "QQQ", "semiconductors": "SMH", "cybersecurity": "CIBR",
    "electrification": "GRID", "nuclear": "URA", "biotech_tools": "XBI",
    "defense_space": "ITA", "healthcare_innov": "XLV", "robotics": "BOTZ",
    "quantum_computing": "QTUM", "critical_minerals": "REMX", "space_satcom": "UFO",
    "autonomy": "IDRV", "genomics": "ARKG", "india_growth": "INDA",
    "africa_growth": "EZA", "energy_storage": "LIT", "weight_loss_glp1": "XLV",
    "water_scarcity": "PHO",
    "legacy_retail": "XRT", "ice_autos": "CARZ", "fossil_fuels": "XLE", "linear_media": "PBS",
    "pharmaceuticals": "XPH", "airlines": "JETS", "homebuilders": "ITB", "chemicals": "XLB",
    "utilities_water_gas": "XLU", "medical_devices": "IHI", "reits_diversified": "VNQ",
    "mining_diversified": "PICK", "gaming": "ESPO", "ecommerce_platforms": "IBUY",
    "fintech_payments": "IPAY", "crypto_infra": "BLOK", "hydrogen": "HDRO",
    "packaged_food": "PBJ", "beverages": "PBJ", "travel_leisure": "PEJ",
    "construction_engineering": "PAVE", "waste_management": "XLI",
}


_CACHE: dict = {"t": 0.0, "val": None}


def industry_markets(*, start: str = "2022-01-01", data=None, ttl: int = 3600,
                      valuation_fn: Optional[Callable[[list], list]] = None,
                      geo_fn: Optional[Callable[[list], list]] = None) -> dict:
    """Per-theme market-cycle map, mirroring global_markets(). Cached `ttl`s. Pass `data` (dict
    etf→Series) for tests. `valuation_fn`/`geo_fn` are optional (see module docstring)."""
    import time
    if data is None and _CACHE["val"] is not None and (time.time() - _CACHE["t"]) < ttl:
        return _CACHE["val"]
    out = _compute(start=start, data=data, valuation_fn=valuation_fn, geo_fn=geo_fn)
    if data is None and "error" not in out:
        _CACHE.update(t=time.time(), val=out)
    return out


def _synthetic_basket(close, tickers: list[str]):
    """Equal-weight index from a theme's own constituent tickers, for themes with no ETF proxy
    at all (mostly narrow/frontier niches). Normalizes each ticker to 1.0 at its first available
    date, then averages across whatever tickers have data on a given day."""
    import pandas as pd
    cols = [t for t in tickers if t in close.columns]
    if not cols:
        return None
    sub = close[cols].dropna(how="all")
    if sub.empty:
        return None
    normed = sub / sub.bfill().iloc[0]
    return normed.mean(axis=1)


def _compute(*, start: str, data=None,
             valuation_fn: Optional[Callable[[list], list]] = None,
             geo_fn: Optional[Callable[[list], list]] = None) -> dict:
    groups = theme_groups()
    etf_by_theme = {k: v for k, v in REPRESENTATIVE_ETF.items() if k in THEME_LABELS}
    # fall back to the theme's first curated proxy ETF (tags.THEME_ETFS) for themes without a
    # hand-picked REPRESENTATIVE_ETF entry, instead of silently rendering blank cards.
    for g in groups:
        key = g["key"]
        if key not in etf_by_theme and g.get("etfs"):
            etf_by_theme[key] = g["etfs"][0]
    etfs = sorted(set(etf_by_theme.values()))
    # themes with neither a curated nor a THEME_ETFS proxy: fall back to a synthetic basket of
    # their own constituent tickers, so genuinely thin/frontier themes still get real data instead
    # of "unknown".
    basket_tickers = sorted({t for g in groups if g["key"] not in etf_by_theme
                              for t in g.get("tickers", [])})
    injected = data is not None
    if data is None:
        close = _download(etfs, start)
        data = {e: (close[e] if e in close.columns else None) for e in etfs}
        if basket_tickers:
            basket_close = _download(basket_tickers, start)
            for g in groups:
                key = g["key"]
                if key not in etf_by_theme and g.get("tickers"):
                    data[f"__basket_{key}"] = _synthetic_basket(basket_close, g["tickers"])

    # skip the extra fundamentals/valuation + per-ticker geo lookups when prices are injected (tests)
    # or the caller didn't wire in valuation_fn/geo_fn — same convention as global_markets.py's pe_fn gating.
    valuation_by_key: dict = {}
    if valuation_fn and not injected:
        valuation_by_key = {v["key"]: v for v in valuation_fn(groups)}

    rows = []
    for g in groups:
        key, label = g["key"], g["label"]
        etf = etf_by_theme.get(key)
        px = data.get(etf) if etf else data.get(f"__basket_{key}")
        m = _metrics(px) if px is not None else None
        geography = geo_fn(g.get("tickers", [])) if (geo_fn and not injected and g.get("tickers")) else []
        base = {"key": key, "label": label, "description": THEME_DESCRIPTIONS.get(key, ""),
                "lifecycle": g.get("lifecycle", "emerging"),
                "etf": etf, "etfs": g.get("etfs", []), "tickers": g.get("tickers", []),
                "geography": geography,
                "valuation": valuation_by_key.get(key, {"n": 0, "verdict": "insufficient_data"})}
        if m is None:
            base.update({"phase": "unknown", "color": PHASES["unknown"]["color"]})
            rows.append(base)
            continue
        fwd = _forward_lean(m)
        base.update({"phase": m["phase"], "color": PHASES[m["phase"]]["color"],
                    "mom6_pct": round(m["mom6"] * 100, 1), "mom1_pct": round(m["mom1"] * 100, 1),
                    "efficiency": m["efficiency"], "above_200d": m["above200"],
                    "forward_lean": fwd["lean"], "accel": fwd["accel"],
                    "past": _past_phases(px), "seasonality": monthly_seasonality(px)})
        rows.append(base)

    ranked = sorted([r for r in rows if "mom6_pct" in r], key=lambda x: x["mom6_pct"])
    n = len(ranked)
    for i, r in enumerate(ranked):
        r["rel_strength"] = round((i + 1) / n, 2) if n else None

    leaders = sorted([r for r in rows if "rel_strength" in r], key=lambda x: -x["rel_strength"])
    return {
        "as_of": _as_of(data, etfs), "industries": rows, "phases": PHASES, "season_scale": SEASON_SCALE,
        "leaders": [{"label": r["label"], "phase": r["phase"], "mom6_pct": r["mom6_pct"]} for r in leaders[:5]],
        "laggards": [{"label": r["label"], "phase": r["phase"], "mom6_pct": r["mom6_pct"]}
                     for r in leaders[-5:][::-1]],
        "note": ("Market-cycle PHASE per secular theme from its proxy ETF: same trend/momentum signals as "
                 "global_markets.py's country map. rel_strength ranks the rotation across themes. valuation "
                 "(when a valuation_fn is wired in) is a fair-value-based verdict aggregated across each theme's "
                 "curated constituent tickers — undervalued/fair/overvalued, not a relative-cheapness percentile "
                 "like the country map. geography (when a geo_fn is wired in) = HQ-country breakdown of each "
                 "theme's constituents (where the industry actually lives), not investment flows. lifecycle "
                 "tags each theme 'emerging' (secular-growth) or 'fading' (structurally shrinking, being "
                 "displaced by an emerging theme elsewhere in this map) — see tags.THEME_LIFECYCLE."),
    }


def _as_of(data, etfs) -> str:
    for e in etfs:
        s = data.get(e)
        if s is not None and len(s.dropna()):
            return str(s.dropna().index[-1])[:10]
    return ""


def _synthetic_index(series_list):
    """Equal-weight synthetic basket: normalize each series to 100 at its own first value, then
    average across the basket (skipping NaN) — a stand-in index for a subsector with no real ETF."""
    import pandas as pd
    aligned = pd.concat([s.dropna() / s.dropna().iloc[0] * 100 for s in series_list if len(s.dropna())], axis=1)
    return aligned.mean(axis=1).dropna()


_DETAIL_CACHE: dict = {}


def industry_theme_detail(key: str, *, start: str = "2022-01-01", data=None, ttl: int = 3600) -> dict:
    """Drill-down for one theme: its subsectors (or, for themes with no curated split, each
    constituent ticker) get their OWN phase read — same engine as the top-level ETF proxy, applied
    to a synthetic equal-weight basket of that subsector's tickers (real ETFs don't exist at this
    granularity). `overall` mirrors the theme's row from industry_markets(). Cached `ttl`s per key.
    Pass `data` (dict ticker→Series) to test the per-ticker/subsector path without network — this
    also skips `overall` (which would otherwise call the network-hitting industry_markets())."""
    import time
    cached = _DETAIL_CACHE.get(key)
    if data is None and cached and (time.time() - cached["t"]) < ttl:
        return cached["val"]
    out = _compute_detail(key, start=start, data=data)
    if data is None and "error" not in out:
        _DETAIL_CACHE[key] = {"t": time.time(), "val": out}
    return out


def _compute_detail(key: str, *, start: str, data=None) -> dict:
    if key not in THEME_LABELS:
        return {"error": f"unknown theme '{key}'"}
    groups = {g["key"]: g for g in theme_groups()}
    g = groups[key]
    tickers = g["tickers"]

    injected = data is not None
    overall = None
    if not injected:
        overall_all = industry_markets(start=start)
        overall = next((r for r in overall_all["industries"] if r["key"] == key), None)

    base = {"key": key, "label": g["label"], "description": g["description"], "lifecycle": g["lifecycle"],
            "etf": REPRESENTATIVE_ETF.get(key), "overall": overall}
    if not tickers:
        return {**base, "subsectors": None, "tickers": [], "as_of": "",
                "note": "No curated tickers for this theme yet — see overall for the ETF-proxy read."}

    if data is None:
        close = _download(tickers, start)
        data = {t: (close[t] if t in close.columns else None) for t in tickers}

    ticker_rows = []
    for t in tickers:
        px = data.get(t)
        m = _metrics(px) if px is not None else None
        if m is None:
            ticker_rows.append({"symbol": t, "phase": "unknown", "color": PHASES["unknown"]["color"]})
            continue
        ticker_rows.append({"symbol": t, "phase": m["phase"], "color": PHASES[m["phase"]]["color"],
                             "mom6_pct": round(m["mom6"] * 100, 1), "mom1_pct": round(m["mom1"] * 100, 1),
                             "efficiency": m["efficiency"], "above_200d": m["above200"]})
    ticker_by_symbol = {r["symbol"]: r for r in ticker_rows}

    subsector_map = subsectors_for(key)
    subsectors = None
    if subsector_map:
        by_name: dict[str, list[str]] = {}
        for sym in tickers:
            by_name.setdefault(subsector_map.get(sym, "Other"), []).append(sym)
        subsectors = []
        for name, syms in sorted(by_name.items(), key=lambda kv: (kv[0] == "Other", kv[0])):
            syms = sorted(syms)
            series_list = [data[s] for s in syms if data.get(s) is not None and len(data[s].dropna())]
            synthetic = _synthetic_index(series_list) if series_list else None
            m = _metrics(synthetic) if synthetic is not None else None
            row = {"name": name, "tickers": syms, "ticker_detail": [ticker_by_symbol[s] for s in syms]}
            if m is None:
                row.update({"phase": "unknown", "color": PHASES["unknown"]["color"]})
            else:
                fwd = _forward_lean(m)
                row.update({"phase": m["phase"], "color": PHASES[m["phase"]]["color"],
                            "mom6_pct": round(m["mom6"] * 100, 1), "mom1_pct": round(m["mom1"] * 100, 1),
                            "efficiency": m["efficiency"], "above_200d": m["above200"],
                            "forward_lean": fwd["lean"], "accel": fwd["accel"], "past": _past_phases(synthetic)})
            subsectors.append(row)

    return {**base, "subsectors": subsectors, "tickers": None if subsectors else ticker_rows,
            "as_of": _as_of(data, tickers),
            "note": ("Subsector/ticker phase reads use the SAME trend/momentum engine as the theme-level ETF "
                     "proxy, applied per-name (or to a synthetic equal-weight basket for a subsector) since no "
                     "real ETF exists at this granularity. 'overall' is the theme's actual ETF-proxy row from "
                     "industry_markets() for comparison. Themes with no curated subsector split (see tags."
                     "_SUBSECTORS) list each constituent ticker flat instead.")}
