"""Sector/theme tagging: curated theme membership + sector passthrough."""
from market_traits.tags import tag_symbol, theme_groups, themes_for


def test_themes_for_known_and_unknown_ticker():
    assert "semiconductors" in themes_for("NVDA")
    assert "ai_infra" in themes_for("NVDA")
    assert themes_for("UNKNOWNTICKER") == []


def test_tag_symbol_returns_sector_and_themes():
    sector, themes = tag_symbol("PANW", {"sector": "Technology"})
    assert sector == "Technology"
    assert "cybersecurity" in themes


def test_theme_groups_shape():
    groups = theme_groups()
    assert groups
    keys = {g["key"] for g in groups}
    assert "ai_infra" in keys and "semiconductors" in keys
    ai = next(g for g in groups if g["key"] == "ai_infra")
    assert "NVDA" in ai["tickers"]
    assert ai["etfs"]
