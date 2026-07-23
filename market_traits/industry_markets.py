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
from market_traits.tags import THEME_DESCRIPTIONS, THEME_LABELS, theme_groups

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


def _compute(*, start: str, data=None,
             valuation_fn: Optional[Callable[[list], list]] = None,
             geo_fn: Optional[Callable[[list], list]] = None) -> dict:
    groups = theme_groups()
    etf_by_theme = {k: v for k, v in REPRESENTATIVE_ETF.items() if k in THEME_LABELS}
    etfs = sorted(set(etf_by_theme.values()))
    injected = data is not None
    if data is None:
        close = _download(etfs, start)
        data = {e: (close[e] if e in close.columns else None) for e in etfs}

    # skip the extra fundamentals/valuation + per-ticker geo lookups when prices are injected (tests)
    # or the caller didn't wire in valuation_fn/geo_fn — same convention as global_markets.py's pe_fn gating.
    valuation_by_key: dict = {}
    if valuation_fn and not injected:
        valuation_by_key = {v["key"]: v for v in valuation_fn(groups)}

    rows = []
    for g in groups:
        key, label = g["key"], g["label"]
        etf = etf_by_theme.get(key)
        px = data.get(etf) if etf else None
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
