"""Calendar-month seasonality — reused by both global_markets.py and industry_markets.py.

Given a price series already in memory (no extra fetch — the caller already downloaded it for
phase/momentum), reports the historical average return for each calendar month (Jan..Dec) across
every year on record, with a t-stat and year count so a thin sample (e.g. a country ETF with only
4 years of history) reads as "not enough data" rather than a confident-looking number.

Honest scope: this is the oldest, most arbitraged anomaly class there is (see
backend/analytics/calendar_edges.py's day-of-week/turn-of-month cousin) — no PBO/overfit gate here,
it's presented as a descriptive historical average, not a certified edge.
"""
from __future__ import annotations

import math

_MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Diverging color bands keyed off the t-stat magnitude/sign — mirrors PHASES' "constants dict,
# echoed straight to the frontend" pattern in global_markets.py, so the legend has one source of truth.
SEASON_SCALE = {
    "strong_positive": {"label": "Strong positive (t≥2)", "color": "#16a34a"},
    "positive":        {"label": "Positive (t≥0.5)",       "color": "#86efac"},
    "flat":            {"label": "Flat (|t|<0.5)",         "color": "#6b7280"},
    "negative":        {"label": "Negative (t≤-0.5)",      "color": "#fca5a5"},
    "strong_negative": {"label": "Strong negative (t≤-2)", "color": "#ef4444"},
    "insufficient":    {"label": "Not enough history",     "color": "#252b36"},
}


def _band(t: float) -> str:
    if t >= 2:
        return "strong_positive"
    if t >= 0.5:
        return "positive"
    if t <= -2:
        return "strong_negative"
    if t <= -0.5:
        return "negative"
    return "flat"


def monthly_seasonality(px, *, min_years: int = 3) -> list[dict]:
    """Pure: average calendar-month return (%) across all years in `px`'s history.

    Returns 12 entries (Jan..Dec) in calendar order. A month with fewer than `min_years` observed
    years reports band="insufficient" rather than a noisy mean.
    """
    px = px.dropna()
    if len(px) < 30:
        return [{"month": i + 1, "label": lbl, "avg_pct": None, "t": None, "n": 0,
                 "band": "insufficient", "color": SEASON_SCALE["insufficient"]["color"]}
                for i, lbl in enumerate(_MONTH_LABELS)]

    monthly = px.resample("ME").last().dropna()
    monthly_ret = monthly.pct_change().dropna() * 100  # % return per month-end
    by_month: dict[int, list] = {m: [] for m in range(1, 13)}
    for dt, r in monthly_ret.items():
        by_month[dt.month].append(float(r))

    out = []
    for i, lbl in enumerate(_MONTH_LABELS):
        vals = by_month[i + 1]
        n = len(vals)
        if n < min_years:
            out.append({"month": i + 1, "label": lbl, "avg_pct": None, "t": None, "n": n,
                       "band": "insufficient", "color": SEASON_SCALE["insufficient"]["color"]})
            continue
        mean = sum(vals) / n
        sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / (n - 1)) if n > 1 else 0.0
        t = (mean / sd * math.sqrt(n)) if sd > 0 else 0.0
        band = _band(t)
        out.append({"month": i + 1, "label": lbl, "avg_pct": round(mean, 2), "t": round(t, 2), "n": n,
                   "band": band, "color": SEASON_SCALE[band]["color"]})
    return out
