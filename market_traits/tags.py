"""Sector + secular-theme tagging for the long-term screen (DN-56).

Two orthogonal labels per name:
  - `sector`: yfinance's GICS-ish sector string (for the cyclical-risk flag and
    the sector cap in portfolio construction). Data-driven, no curation.
  - `themes`: the secular baskets the long-term thesis actually cares about
    (AI infra, semis, cybersecurity, electrification/grid, nuclear/uranium,
    biotech tools, defense/space, healthcare innovation). These are NOT in
    yfinance, so they are a small curated map keyed by ticker. Unknown tickers
    simply carry no theme — this is a convenience layer, not a source of truth.

Keep the map honest and small: only add a ticker when its membership is
unambiguous. A name can belong to several themes (NVDA = ai_infra + semiconductors).
"""
from __future__ import annotations

# Human-readable theme labels (stable keys → display names).
THEME_LABELS: dict[str, str] = {
    "ai_infra": "AI infrastructure",
    "semiconductors": "Semiconductors",
    "cybersecurity": "Cybersecurity",
    "electrification": "Electrification / grid",
    "nuclear": "Nuclear / uranium",
    "biotech_tools": "Biotech tools",
    "defense_space": "Defense / space",
    "healthcare_innov": "Healthcare innovation",
    "robotics": "Robotics & automation",
    "quantum_computing": "Quantum computing",
    "critical_minerals": "Critical minerals / rare earth",
    "space_satcom": "Space / satellite comms",
    "autonomy": "Autonomous vehicles",
    "genomics": "Genomics / gene editing",
    "india_growth": "India growth",
    "africa_growth": "Africa growth",
    "energy_storage": "Energy storage / batteries",
    "weight_loss_glp1": "GLP-1 / weight-loss drugs",
    "water_scarcity": "Water scarcity / infrastructure",
}

# One-line thesis per theme — why it's a secular basket, not just a sector label.
THEME_DESCRIPTIONS: dict[str, str] = {
    "ai_infra": "Compute, accelerators, networking and hyperscale capex behind the AI buildout.",
    "semiconductors": "Design, equipment and foundry — the picks-and-shovels of every compute cycle.",
    "cybersecurity": "Attack surface grows with every cloud migration; spend is famously non-discretionary.",
    "electrification": "Grid buildout, renewables and power infrastructure driven by AI-datacenter and EV load growth.",
    "nuclear": "Uranium/SMR revival as datacenter and grid demand outgrows renewables-only supply.",
    "biotech_tools": "Sequencing, reagents and instruments — sells to every drug developer regardless of which drugs win.",
    "defense_space": "Rearmament cycle + commercial space access, both multi-decade government-backed demand.",
    "healthcare_innov": "Novel drug modalities and med-tech platforms with structural pricing power.",
    "robotics": "Industrial, surgical and logistics automation as labor costs and reshoring both push adoption.",
    "quantum_computing": "Early-stage compute paradigm; high risk, optionality on a multi-decade horizon.",
    "critical_minerals": "The supply-chain bottleneck shared by EVs, robotics, nuclear and defense.",
    "space_satcom": "Commercial launch cost collapse unlocking satellite broadband and earth observation.",
    "autonomy": "Sensors and compute for self-driving — a slower-than-hyped but structural adoption curve.",
    "genomics": "Gene editing and sequencing-driven therapeutics, distinct from the tools that serve them.",
    "india_growth": "Demographic dividend + formalizing economy, the deepest liquid US-listed EM bench.",
    "africa_growth": "Frontier-market growth option; thin, illiquid US-listed exposure by necessity.",
    "energy_storage": "Grid-scale and behind-the-meter batteries needed to firm intermittent renewables.",
    "weight_loss_glp1": "GLP-1 obesity/diabetes drugs — the fastest-growing pharma category in decades.",
    "water_scarcity": "Aging infrastructure + scarcity economics in utilities, filtration and treatment.",
}

# Curated ticker → themes. Deliberately conservative; extend as conviction warrants.
_THEME_MAP: dict[str, tuple[str, ...]] = {
    # AI infrastructure (compute, accelerators, networking, hyperscale)
    "NVDA": ("ai_infra", "semiconductors"),
    "AMD": ("ai_infra", "semiconductors"),
    "AVGO": ("ai_infra", "semiconductors"),
    "MRVL": ("ai_infra", "semiconductors"),
    "SMCI": ("ai_infra",),
    "DELL": ("ai_infra",),
    "ANET": ("ai_infra",),
    "MSFT": ("ai_infra",),
    "GOOGL": ("ai_infra",),
    "AMZN": ("ai_infra",),
    "META": ("ai_infra",),
    "VRT": ("ai_infra", "electrification"),
    # Semiconductors (broad — design, equipment, foundry)
    "TSM": ("semiconductors",),
    "ASML": ("semiconductors",),
    "AMAT": ("semiconductors",),
    "LRCX": ("semiconductors",),
    "KLAC": ("semiconductors",),
    "MU": ("semiconductors",),
    "TXN": ("semiconductors",),
    "QCOM": ("semiconductors",),
    "ARM": ("semiconductors", "ai_infra"),
    # Cybersecurity
    "PANW": ("cybersecurity",),
    "CRWD": ("cybersecurity",),
    "ZS": ("cybersecurity",),
    "FTNT": ("cybersecurity",),
    "S": ("cybersecurity",),
    "OKTA": ("cybersecurity",),
    "NET": ("cybersecurity",),
    # Electrification / grid
    "ETN": ("electrification",),
    "PWR": ("electrification",),
    "GEV": ("electrification", "nuclear"),
    "NEE": ("electrification",),
    "ENPH": ("electrification", "energy_storage"),
    "FSLR": ("electrification",),
    "TSLA": ("electrification", "energy_storage"),
    # Energy storage / batteries (grid-scale + behind-the-meter)
    "FLNC": ("energy_storage",),
    "STEM": ("energy_storage",),
    "BE": ("energy_storage",),
    # Nuclear / uranium
    "CCJ": ("nuclear",),
    "UEC": ("nuclear",),
    "LEU": ("nuclear",),
    "SMR": ("nuclear",),
    "BWXT": ("nuclear", "defense_space"),
    "URA": ("nuclear",),
    "URNM": ("nuclear",),
    # Biotech tools (picks-and-shovels: sequencing, reagents, instruments)
    "TMO": ("biotech_tools", "healthcare_innov"),
    "DHR": ("biotech_tools", "healthcare_innov"),
    "A": ("biotech_tools",),
    "ILMN": ("biotech_tools",),
    "RGEN": ("biotech_tools",),
    "IQV": ("biotech_tools", "healthcare_innov"),
    # Defense / space
    "LMT": ("defense_space",),
    "RTX": ("defense_space",),
    "NOC": ("defense_space",),
    "GD": ("defense_space",),
    "LHX": ("defense_space",),
    "RKLB": ("defense_space", "space_satcom"),
    "PLTR": ("defense_space", "ai_infra"),
    # Healthcare innovation (novel modalities, med-tech platforms)
    "LLY": ("healthcare_innov", "weight_loss_glp1"),
    "NVO": ("healthcare_innov", "weight_loss_glp1"),
    "ISRG": ("healthcare_innov", "robotics"),
    "VRTX": ("healthcare_innov",),
    "REGN": ("healthcare_innov",),
    # GLP-1 / weight-loss drugs (LLY, NVO already tagged above)
    "VKTX": ("weight_loss_glp1",),
    "AMGN": ("weight_loss_glp1", "healthcare_innov"),
    # Robotics & automation (industrial + surgical + logistics)
    "ROK": ("robotics",),
    "TER": ("robotics",),
    "CGNX": ("robotics",),
    "ZBRA": ("robotics",),
    "SYM": ("robotics",),
    "NOVT": ("robotics",),
    "PATH": ("robotics", "ai_infra"),
    "ABB": ("robotics", "electrification"),
    # Quantum computing (pure-plays + incumbents with named programs)
    "IONQ": ("quantum_computing",),
    "RGTI": ("quantum_computing",),
    "QBTS": ("quantum_computing",),
    "QUBT": ("quantum_computing",),
    "IBM": ("quantum_computing",),
    # Critical minerals / rare earth (the supply-chain bottleneck for EVs, robotics, nuclear, defense)
    "ALB": ("critical_minerals",),
    "MP": ("critical_minerals",),
    "FCX": ("critical_minerals",),
    "SQM": ("critical_minerals",),
    "LAC": ("critical_minerals",),
    # Space / satellite comms (commercial launch + satcom, separate from defense primes)
    "ASTS": ("space_satcom",),
    "IRDM": ("space_satcom",),
    "GSAT": ("space_satcom",),
    "VSAT": ("space_satcom",),
    # Autonomous vehicles (sensors, compute, platform — pure-plays; TSLA stays electrification-only)
    "MBLY": ("autonomy",),
    "AEVA": ("autonomy",),
    "LAZR": ("autonomy",),
    "OUST": ("autonomy",),
    # Genomics / gene editing (distinct from biotech_tools' picks-and-shovels)
    "CRSP": ("genomics",),
    "NTLA": ("genomics",),
    "BEAM": ("genomics",),
    "EDIT": ("genomics",),
    # India growth (ADRs — the emerging-market thesis with the deepest liquid US-listed bench)
    "INFY": ("india_growth",),
    "WIT": ("india_growth",),
    "HDB": ("india_growth",),
    "IBN": ("india_growth",),
    # Africa growth (few pure US-listed African names; these two are the liquid ADRs)
    "GFI": ("africa_growth",),
    "SSL": ("africa_growth",),
    # Water scarcity / infrastructure (utilities, filtration, treatment)
    "XYL": ("water_scarcity",),
    "AWK": ("water_scarcity",),
    "PNR": ("water_scarcity",),
    "CWT": ("water_scarcity",),
}

# Optional finer-grained grouping WITHIN a theme — {theme: {ticker: subsector label}}.
# Only populated for themes crowded/heterogeneous enough that a flat ticker list
# hides the actual split (e.g. "AI infra" = accelerators vs hyperscalers vs cooling,
# not one basket). Tickers absent from a theme's map fall into "Other" if the theme
# has ANY subsectors defined, else the theme just renders flat.
_SUBSECTORS: dict[str, dict[str, str]] = {
    "ai_infra": {
        "NVDA": "Accelerators", "AMD": "Accelerators",
        "AVGO": "Accelerators & networking", "MRVL": "Accelerators & networking", "ANET": "Networking",
        "SMCI": "Servers", "DELL": "Servers",
        "MSFT": "Hyperscale cloud", "GOOGL": "Hyperscale cloud", "AMZN": "Hyperscale cloud", "META": "Hyperscale cloud",
        "VRT": "Datacenter power & cooling",
        "ARM": "Chip IP", "PLTR": "AI software/platforms", "PATH": "AI software/platforms",
    },
    "semiconductors": {
        "TSM": "Foundry",
        "ASML": "Equipment", "AMAT": "Equipment", "LRCX": "Equipment", "KLAC": "Equipment",
        "MU": "Memory", "TXN": "Analog/legacy", "QCOM": "Mobile/wireless", "ARM": "Design (IP)",
        "NVDA": "Design (fabless)", "AMD": "Design (fabless)", "AVGO": "Design (fabless)", "MRVL": "Design (fabless)",
    },
    "defense_space": {
        "LMT": "Primes", "RTX": "Primes", "NOC": "Primes", "GD": "Primes", "LHX": "Primes",
        "BWXT": "Naval/nuclear propulsion", "RKLB": "Commercial space", "PLTR": "Defense software",
    },
    "nuclear": {
        "CCJ": "Uranium miners", "UEC": "Uranium miners",
        "LEU": "Enrichment/fuel", "SMR": "SMR developers",
        "BWXT": "Nuclear components", "GEV": "Utility-scale reactors",
    },
    "healthcare_innov": {
        "LLY": "Pharma — GLP-1/metabolic", "NVO": "Pharma — GLP-1/metabolic",
        "VRTX": "Pharma — specialty", "REGN": "Pharma — biologics", "AMGN": "Pharma — biologics",
        "ISRG": "Med-tech / surgical robotics",
        "TMO": "Tools/instruments", "DHR": "Tools/instruments", "IQV": "CRO/services",
    },
    "robotics": {
        "ROK": "Industrial automation", "ABB": "Industrial automation",
        "TER": "Test/automation equipment", "CGNX": "Machine vision",
        "ZBRA": "Logistics/tracking", "SYM": "Warehouse robotics", "NOVT": "Precision motion",
        "PATH": "Software (RPA)", "ISRG": "Surgical robotics",
    },
    "critical_minerals": {
        "ALB": "Lithium", "SQM": "Lithium", "LAC": "Lithium",
        "MP": "Rare earths", "FCX": "Copper",
    },
}

# Curated theme ETFs → the theme they proxy (for the ETF/theme backtest layer).
THEME_ETFS: dict[str, str] = {
    "SMH": "semiconductors", "SOXX": "semiconductors",
    "BUG": "cybersecurity", "CIBR": "cybersecurity", "HACK": "cybersecurity",
    "GRID": "electrification", "PAVE": "electrification", "TAN": "electrification",
    "URA": "nuclear", "URNM": "nuclear", "NLR": "nuclear",
    "XBI": "biotech_tools", "IBB": "biotech_tools",
    "ITA": "defense_space", "XAR": "defense_space", "ROKT": "defense_space",
    "QQQ": "ai_infra", "IGV": "ai_infra", "AIQ": "ai_infra",
    "XLV": "healthcare_innov", "IHI": "healthcare_innov",
    "BOTZ": "robotics", "ROBO": "robotics",
    "QTUM": "quantum_computing",
    "REMX": "critical_minerals", "LIT": "critical_minerals", "PICK": "critical_minerals",
    "UFO": "space_satcom", "ARKX": "space_satcom",
    "IDRV": "autonomy", "DRIV": "autonomy",
    "ARKG": "genomics",
    "INDA": "india_growth", "EPI": "india_growth",
    "AFK": "africa_growth", "EZA": "africa_growth",
    "PHO": "water_scarcity", "CGW": "water_scarcity",
}


def themes_for(symbol: str) -> list:
    """Curated secular themes for a ticker (empty if unknown)."""
    return list(_THEME_MAP.get(symbol.upper(), ()))


def tag_symbol(symbol: str, info: dict | None) -> tuple[str, list]:
    """Return (sector, themes) for a symbol. Sector from yfinance; themes curated."""
    sector = (info or {}).get("sector") or ""
    return sector, themes_for(symbol)


def theme_groups() -> list[dict]:
    """Static, no-fetch view of the curated themes for the Future Industries tab.

    Each group lists its member tickers + ETF proxies, straight from the curated
    maps above — no yfinance calls, so this is instant unlike the factor screen
    (which only scores a narrow universe most theme tickers aren't even in).
    """
    tickers_by_theme: dict[str, list[str]] = {}
    for sym, themes in _THEME_MAP.items():
        for t in themes:
            tickers_by_theme.setdefault(t, []).append(sym)
    etfs_by_theme: dict[str, list[str]] = {}
    for etf, theme in THEME_ETFS.items():
        etfs_by_theme.setdefault(theme, []).append(etf)

    groups = []
    for key, label in THEME_LABELS.items():
        tickers = sorted(tickers_by_theme.get(key, []))
        theme_subsectors = _SUBSECTORS.get(key, {})
        subsectors = None
        if theme_subsectors:
            by_name: dict[str, list[str]] = {}
            for sym in tickers:
                name = theme_subsectors.get(sym, "Other")
                by_name.setdefault(name, []).append(sym)
            subsectors = [
                {"name": name, "tickers": sorted(syms)}
                for name, syms in sorted(by_name.items(), key=lambda kv: (kv[0] == "Other", kv[0]))
            ]
        groups.append({
            "key": key,
            "label": label,
            "description": THEME_DESCRIPTIONS.get(key, ""),
            "tickers": tickers,
            "subsectors": subsectors,
            "etfs": sorted(etfs_by_theme.get(key, [])),
        })
    return groups
