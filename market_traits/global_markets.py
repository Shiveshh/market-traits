"""Global market rotation map — where in the business cycle is each country's market?

The macro thesis: capital rotates. When one economy contracts another expands, and the money flows to the market with
the strongest trend. This module reads a basket of single-country equity indices (via free country ETFs) and places
each into a market-cycle PHASE — booming · expanding · slowing · recession · recovering — from the same trend/momentum
signals the market_weather module uses (price vs 200d, 6-/3-/1-month momentum, Kaufman efficiency). It reports the
CURRENT phase (for the world map), a PAST monthly phase history, and a FORWARD lean (momentum acceleration + relative
strength — a tilt, honestly, not a forecast).

~49 markets is the practical CEILING of free single-country equity data. Free daily data; injectable.

Relative-valuation (trailingPE percentile) needs a per-symbol fundamentals lookup this package doesn't own — pass
`pe_fn: Callable[[list[str]], dict[str, float | None]]` to wire one in (a consumer's own cached .info fetch). Without
it, valuation_pctile/valuation_label are simply omitted.
"""
from __future__ import annotations

from typing import Callable, Optional

from market_traits.market_weather import _efficiency_ratio
from market_traits.seasonality import SEASON_SCALE, monthly_seasonality

# country → (ISO2, display, country ETF [data], index-CFD symbol on FTMO/FundedNext or None, tile row, tile col).
# tile (row,col) lays the markets on a coarse 6×12 world grid (west→east, north→south) for the map — not exact geo.
COUNTRIES = [
    ("US", "United States", "SPY", "US500",  1, 2),
    ("CA", "Canada",        "EWC", None,      0, 2),
    ("MX", "Mexico",        "EWW", None,      2, 2),
    ("BR", "Brazil",        "EWZ", None,      3, 3),
    ("GB", "UK",            "EWU", "UK100",   1, 5),
    ("DE", "Germany",       "EWG", "GER40",   1, 6),
    ("FR", "France",        "EWQ", "FRA40",   2, 5),
    ("EU", "Eurozone",      "EZU", "EU50",    1, 6),
    ("CH", "Switzerland",   "EWL", "SUI20",   2, 6),
    ("ES", "Spain",         "EWP", "SPA35",   2, 5),
    ("IT", "Italy",         "EWI", "ITA40",   2, 6),
    ("NL", "Netherlands",   "EWN", "NLD25",   1, 6),
    ("ZA", "South Africa",  "EZA", None,      4, 6),
    ("SA", "Saudi Arabia",  "KSA", None,      2, 7),
    ("IN", "India",         "INDA", "INDIA50", 2, 8),
    ("CN", "China",         "FXI", "CHINA50", 2, 9),
    ("HK", "Hong Kong",     "EWH", "HK50",    2, 9),
    ("JP", "Japan",         "EWJ", "JP225",   1, 10),
    ("KR", "South Korea",   "EWY", None,      1, 10),
    ("TW", "Taiwan",        "EWT", None,      2, 10),
    ("SG", "Singapore",     "EWS", None,      3, 9),
    ("AU", "Australia",     "EWA", "AUS200",  4, 10),
    # broader coverage (free country ETFs; most emerging markets have no FTMO/FundedNext index CFD → not tradeable)
    ("ID", "Indonesia",     "EIDO", None,     0, 0),
    ("TH", "Thailand",      "THD", None,      0, 0),
    ("MY", "Malaysia",      "EWM", None,      0, 0),
    ("PH", "Philippines",   "EPHE", None,     0, 0),
    ("VN", "Vietnam",       "VNM", None,      0, 0),
    ("TR", "Turkey",        "TUR", None,      0, 0),
    ("PL", "Poland",        "EPOL", "POL",    0, 0),
    ("SE", "Sweden",        "EWD", "SWE30",   0, 0),
    ("NO", "Norway",        "NORW", "NOR25",  0, 0),
    ("IL", "Israel",        "EIS", None,      0, 0),
    ("CL", "Chile",         "ECH", None,      0, 0),
    ("PE", "Peru",          "EPU", None,      0, 0),
    ("CO", "Colombia",      "GXG", None,      0, 0),
    ("AR", "Argentina",     "ARGT", None,     0, 0),
    ("GR", "Greece",        "GREK", None,     0, 0),
    ("AT", "Austria",       "EWO", "AUT20",   0, 0),
    ("BE", "Belgium",       "EWK", "BEL20",   0, 0),
    ("IE", "Ireland",       "EIRL", None,     0, 0),
    ("DK", "Denmark",       "EDEN", "DEN25",  0, 0),
    ("PT", "Portugal",      "PGAL", "PT",     0, 0),
    ("NZ", "New Zealand",   "ENZL", None,     0, 0),
    ("EG", "Egypt",         "EGPT", None,     0, 0),
    ("QA", "Qatar",         "QAT", None,      0, 0),
    ("AE", "UAE",           "UAE", None,      0, 0),
    ("NG", "Nigeria",       "NGE", None,      0, 0),
    ("KW", "Kuwait",        "KWT", None,      0, 0),
    ("PK", "Pakistan",      "PAK", None,      0, 0),
]

# ISO 3166-1 numeric code per market → the join key for a geographic world map (world-atlas uses numeric ids).
# Eurozone (EU) is an aggregate, not a country, so it has no numeric id (stays in the table, off the map).
ISO_NUM = {
    "US": "840", "CA": "124", "MX": "484", "BR": "076", "GB": "826", "DE": "276", "FR": "250", "CH": "756",
    "ES": "724", "IT": "380", "NL": "528", "ZA": "710", "SA": "682", "IN": "356", "CN": "156", "HK": "344",
    "JP": "392", "KR": "410", "TW": "158", "SG": "702", "AU": "036",
    "ID": "360", "TH": "764", "MY": "458", "PH": "608", "VN": "704", "TR": "792", "PL": "616", "SE": "752",
    "NO": "578", "IL": "376", "CL": "152", "PE": "604", "CO": "170", "AR": "032", "GR": "300", "AT": "040",
    "BE": "056", "IE": "372", "DK": "208", "PT": "620", "NZ": "554", "EG": "818", "QA": "634", "AE": "784",
    "NG": "566", "KW": "414", "PK": "586",
}

# Sub-markets: narrower segment/exchange ETFs WITHIN a country, for the drill-down detail page —
# e.g. the US isn't one market, it's Nasdaq growth vs Dow industrials vs Russell small-cap. Curated
# conservatively: only added where a liquid, well-established free-data ETF exists. Most countries
# have none yet (empty list) — the detail page then just shows the country's overall read.
SUB_MARKETS: dict[str, list[tuple[str, str]]] = {
    "US": [("Nasdaq 100 (large-cap tech)", "QQQ"), ("Dow Jones Industrials", "DIA"), ("Russell 2000 (small-cap)", "IWM")],
    "CN": [("China A-shares (onshore)", "ASHR"), ("China internet", "KWEB")],
    "JP": [("Japan small-cap", "SCJ")],
    "IN": [("India small-cap", "SMIN")],
    "GB": [("UK small-cap", "EWUS")],
    "BR": [("Brazil small-cap", "BRF")],
    "EU": [("Europe small-cap", "DFE")],
}

# phase → (display label, cycle rank for sorting, hex for the map). Warm = expanding, cool = contracting.
PHASES = {
    "booming":    {"label": "Booming",    "rank": 5, "color": "#16a34a"},
    "expanding":  {"label": "Expanding",  "rank": 4, "color": "#65a30d"},
    "slowing":    {"label": "Slowing",    "rank": 3, "color": "#eab308"},
    "recovering": {"label": "Recovering", "rank": 2, "color": "#0ea5e9"},
    "recession":  {"label": "Recession",  "rank": 1, "color": "#ef4444"},
    "unknown":    {"label": "No data",    "rank": 0, "color": "#6b7280"},
}


def _download(symbols, start):
    import yfinance as yf
    import pandas as pd
    df = yf.download(symbols, start=start, interval="1d", auto_adjust=True, progress=False)
    close = df["Close"] if isinstance(df.columns, pd.MultiIndex) else df[["Close"]].rename(columns={"Close": symbols[0]})
    return close


def _valuation_label(pctile: float) -> str:
    """`pctile` follows valuation_pctile's convention: 1.0 = cheapest (lowest PE) among covered
    markets, 0.0 = most expensive — so a LOW pctile is the expensive end."""
    if pctile <= 1 / 3:
        return "expensive"
    if pctile >= 2 / 3:
        return "cheap"
    return "mid"


def _phase(above200: bool, mom6: float, mom3: float, mom1: float, er: float) -> str:
    """Business-cycle phase from trend + momentum. Above 200d + rising = expansion side; below + falling = contraction."""
    if above200 and mom6 > 0.03:
        return "booming" if (mom3 > 0.02 and er >= 0.30) else "expanding"
    if not above200 and mom6 < -0.03:
        return "recovering" if mom1 > 0.03 else "recession"
    return "slowing" if mom3 < 0 else "expanding"


def _metrics(px):
    """Trend/momentum snapshot for one country's price series → phase inputs + the numbers."""
    import pandas as pd
    px = px.dropna()
    if len(px) < 130:
        return None
    last = float(px.iloc[-1])
    ma200 = px.rolling(200).mean().iloc[-1]
    above = bool(last > ma200) if pd.notna(ma200) else bool(last > px.mean())
    mom6 = last / float(px.iloc[-126]) - 1
    mom3 = last / float(px.iloc[-63]) - 1
    mom1 = last / float(px.iloc[-21]) - 1
    er = float(_efficiency_ratio(px, 20).iloc[-1])
    return {"above200": above, "mom6": round(mom6, 4), "mom3": round(mom3, 4),
            "mom1": round(mom1, 4), "efficiency": round(er, 3),
            "phase": _phase(above, mom6, mom3, mom1, er)}


def _past_phases(px, months: int = 12) -> list:
    """Phase at each of the last `months` month-ends → the PAST history row."""
    import pandas as pd
    px = px.dropna()
    monthly = px.resample("ME").last().dropna()
    out = []
    for dt in monthly.index[-months:]:
        window = px.loc[:dt]
        m = _metrics(window)
        out.append({"month": str(dt)[:7], "phase": m["phase"] if m else "unknown"})
    return out


def _forward_lean(m: dict) -> dict:
    """A tilt, not a forecast: is momentum ACCELERATING (recent 1m pace vs the prior 2m pace)?"""
    prior_pace = (m["mom3"] - m["mom1"]) / 2.0          # avg monthly pace of months -3..-2
    accel = m["mom1"] - prior_pace
    lean = "improving" if accel > 0.015 else ("deteriorating" if accel < -0.015 else "stable")
    return {"lean": lean, "accel": round(accel, 4)}


_CACHE: dict = {"t": 0.0, "val": None}


def global_markets(*, start: str = "2022-01-01", data=None, ttl: int = 3600,
                    pe_fn: Optional[Callable[[list], dict]] = None) -> dict:
    """Per-country market-cycle map: CURRENT phase (+ relative strength) for the map, PAST monthly phases and a
    FORWARD lean for the table. Cached `ttl`s (heavy: ~22 country ETFs). Pass `data` (dict etf→Series) for tests.
    `pe_fn(etfs) -> {etf: trailingPE|None}` is optional — without it, relative-valuation fields are omitted."""
    import time
    if data is None and _CACHE["val"] is not None and (time.time() - _CACHE["t"]) < ttl:
        return _CACHE["val"]
    out = _compute(start=start, data=data, pe_fn=pe_fn)
    if data is None and "error" not in out:
        _CACHE.update(t=time.time(), val=out)
    return out


def _compute(*, start: str, data=None, pe_fn: Optional[Callable[[list], dict]] = None) -> dict:
    etfs = [c[2] for c in COUNTRIES]
    injected = data is not None
    if data is None:
        close = _download(etfs, start)
        data = {e: (close[e] if e in close.columns else None) for e in etfs}
    # skip the fundamentals round-trip when prices are injected (tests) or no pe_fn was wired in
    pe_by_etf = pe_fn(etfs) if (pe_fn and not injected) else {e: None for e in etfs}

    rows, mom6s = [], []
    for iso, name, etf, cfd, r, cc in COUNTRIES:
        px = data.get(etf)
        m = _metrics(px) if px is not None else None
        if m is None:
            rows.append({"iso": iso, "iso_num": ISO_NUM.get(iso), "country": name, "etf": etf, "index_cfd": cfd,
                         "tradeable": cfd is not None, "row": r, "col": cc, "phase": "unknown",
                         "color": PHASES["unknown"]["color"]})
            continue
        fwd = _forward_lean(m)
        mom6s.append(m["mom6"])
        rows.append({"iso": iso, "iso_num": ISO_NUM.get(iso), "country": name, "etf": etf, "index_cfd": cfd,
                     "tradeable": cfd is not None,
                     "row": r, "col": cc, "phase": m["phase"], "color": PHASES[m["phase"]]["color"],
                     "mom6_pct": round(m["mom6"] * 100, 1), "mom1_pct": round(m["mom1"] * 100, 1),
                     "efficiency": m["efficiency"], "above_200d": m["above200"],
                     "forward_lean": fwd["lean"], "accel": fwd["accel"],
                     "past": _past_phases(px), "pe_ratio": pe_by_etf.get(etf),
                     "seasonality": monthly_seasonality(px)})
    # relative strength: percentile rank of 6-month momentum across the covered markets (the rotation signal)
    ranked = sorted([r for r in rows if "mom6_pct" in r], key=lambda x: x["mom6_pct"])
    n = len(ranked)
    for i, r in enumerate(ranked):
        r["rel_strength"] = round((i + 1) / n, 2)          # 1.0 = strongest market

    # relative valuation: percentile rank of trailingPE among the covered markets that HAVE a PE
    # (lower PE = cheaper vs peers). This is NOT a fair-value verdict — no per-country stock
    # fundamentals exist here — just a relative-cheapness read.
    priced = sorted([r for r in rows if r.get("pe_ratio")], key=lambda x: -x["pe_ratio"])
    np_ = len(priced)
    for i, r in enumerate(priced):
        r["valuation_pctile"] = round((i + 1) / np_, 2)     # 1.0 = cheapest (lowest PE)
        r["valuation_label"] = _valuation_label(r["valuation_pctile"])

    leaders = sorted([r for r in rows if "rel_strength" in r], key=lambda x: -x["rel_strength"])
    return {
        "as_of": _as_of(data, etfs), "countries": rows, "phases": PHASES, "season_scale": SEASON_SCALE,
        "leaders": [{"country": r["country"], "phase": r["phase"], "mom6_pct": r["mom6_pct"],
                     "tradeable": r["tradeable"], "index_cfd": r["index_cfd"]} for r in leaders[:5]],
        "laggards": [{"country": r["country"], "phase": r["phase"], "mom6_pct": r["mom6_pct"]}
                     for r in leaders[-5:][::-1]],
        "note": ("Market-cycle PHASE per country from its equity index (country ETF): price vs 200d + 6/3/1-month "
                 "momentum + Kaufman efficiency. A MARKET-trend proxy for the cycle, not official recession dating. "
                 "rel_strength ranks the rotation — the strongest-trending market is where the money is going. "
                 "'tradeable' = an index CFD exists on FTMO/FundedNext, so the bot could actually trade it. Forward "
                 "lean = momentum acceleration (a tilt, not a forecast). valuation_pctile ranks trailingPE relative "
                 "cheapness vs the OTHER covered markets (not a fair-value verdict). seasonality = historical "
                 "average return per calendar month, descriptive only."),
    }


def _as_of(data, etfs) -> str:
    for e in etfs:
        s = data.get(e)
        if s is not None and len(s.dropna()):
            return str(s.dropna().index[-1])[:10]
    return ""


_SUB_CACHE: dict = {}


def country_submarket_detail(iso: str, *, start: str = "2022-01-01", data=None, ttl: int = 3600) -> dict:
    """Drill-down for one country: its curated sub-markets (see SUB_MARKETS) each get the SAME
    phase read as the top-level country map, applied to their own (real, liquid) ETF — no synthetic
    basket needed here, unlike industry_markets.industry_theme_detail. `overall` mirrors the
    country's row from global_markets(). Cached `ttl`s per iso. Pass `data` (dict etf→Series) to
    test the sub-market path without network — this also skips `overall`."""
    import time
    cached = _SUB_CACHE.get(iso)
    if data is None and cached and (time.time() - cached["t"]) < ttl:
        return cached["val"]
    out = _compute_submarket_detail(iso, start=start, data=data)
    if data is None and "error" not in out:
        _SUB_CACHE[iso] = {"t": time.time(), "val": out}
    return out


def _compute_submarket_detail(iso: str, *, start: str, data=None) -> dict:
    country = next((c for c in COUNTRIES if c[0] == iso), None)
    if country is None:
        return {"error": f"unknown country '{iso}'"}
    _, name, main_etf, cfd, _r, _cc = country
    subs = SUB_MARKETS.get(iso, [])

    injected = data is not None
    overall = None
    if not injected:
        overall_all = global_markets(start=start)
        overall = next((row for row in overall_all["countries"] if row["iso"] == iso), None)

    base = {"iso": iso, "country": name, "etf": main_etf, "index_cfd": cfd, "overall": overall}
    if not subs:
        return {**base, "sub_markets": [], "as_of": "",
                "note": "No curated sub-markets for this country yet — see overall for the country-index read."}

    etfs = [e for _, e in subs]
    if data is None:
        close = _download(etfs, start)
        data = {e: (close[e] if e in close.columns else None) for e in etfs}

    sub_rows = []
    for label, etf in subs:
        px = data.get(etf)
        m = _metrics(px) if px is not None else None
        if m is None:
            sub_rows.append({"label": label, "etf": etf, "phase": "unknown", "color": PHASES["unknown"]["color"]})
            continue
        fwd = _forward_lean(m)
        sub_rows.append({"label": label, "etf": etf, "phase": m["phase"], "color": PHASES[m["phase"]]["color"],
                          "mom6_pct": round(m["mom6"] * 100, 1), "mom1_pct": round(m["mom1"] * 100, 1),
                          "efficiency": m["efficiency"], "above_200d": m["above200"],
                          "forward_lean": fwd["lean"], "accel": fwd["accel"],
                          "past": _past_phases(px), "seasonality": monthly_seasonality(px)})

    return {**base, "sub_markets": sub_rows, "as_of": _as_of(data, etfs),
            "note": ("Sub-market reads use the SAME trend/momentum engine as the country-level map, applied to "
                     "narrower segment/exchange ETFs (e.g. Nasdaq vs Dow vs Russell for the US) where a liquid "
                     "free-data proxy exists. 'overall' is the country's actual index-ETF row from "
                     "global_markets() for comparison. Most countries have none curated yet (see SUB_MARKETS) — "
                     "sub_markets is simply empty.")}
