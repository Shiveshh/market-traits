"""Sector + secular-theme tagging for the long-term screen (DN-56).

Two orthogonal labels per name:
  - `sector`: yfinance's GICS-ish sector string (for the cyclical-risk flag and
    the sector cap in portfolio construction). Data-driven, no curation.
  - `themes`: the secular baskets the long-term thesis actually cares about
    (AI infra, semis, cybersecurity, electrification/grid, nuclear/uranium,
    biotech tools, defense/space, healthcare innovation). These are NOT in
    yfinance, so they are a small curated map keyed by ticker. Unknown tickers
    simply carry no theme — this is a convenience layer, not a source of truth.

Every theme also carries a `lifecycle` tag (see THEME_LIFECYCLE): "emerging"
for secular-growth baskets, "fading" for structurally-shrinking ones (the
"industries going away" side of the Future Industries tab — legacy retail,
ICE autos, fossil-fuel majors, linear/print media). Fading themes are not
short ideas by themselves (some, like the oil majors, still throw off cash
for years) — they mark businesses on the losing side of a secular disruption,
for the same trend/momentum/phase read the emerging themes get.

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
    "bci": "Brain-computer interfaces",
    "nanotechnology": "Nanotechnology",
    "carbon_capture": "Carbon capture & sequestration",
    "vertical_farming": "Vertical / controlled-environment farming",
    "fusion_energy": "Fusion energy",
    "evtol": "eVTOL / urban air mobility",
    "fintech_payments": "Digital payments / fintech infrastructure",
    "hydrogen": "Hydrogen economy",
    "crypto_infra": "Crypto / blockchain infrastructure",
    "additive_manufacturing": "3D printing / additive manufacturing",
    "ev_charging": "EV charging infrastructure",
    # Fading — structurally shrinking, disrupted-by-the-above-themes baskets.
    "legacy_retail": "Legacy brick-and-mortar retail",
    "ice_autos": "Internal-combustion automakers",
    "fossil_fuels": "Fossil-fuel majors",
    "linear_media": "Linear TV / print media",
}

# Lifecycle stage per theme: "emerging" (secular-growth basket) or "fading"
# (structurally shrinking, being displaced by an emerging theme elsewhere in
# this map). Every key in THEME_LABELS must appear here.
THEME_LIFECYCLE: dict[str, str] = {
    "ai_infra": "emerging", "semiconductors": "emerging", "cybersecurity": "emerging",
    "electrification": "emerging", "nuclear": "emerging", "biotech_tools": "emerging",
    "defense_space": "emerging", "healthcare_innov": "emerging", "robotics": "emerging",
    "quantum_computing": "emerging", "critical_minerals": "emerging", "space_satcom": "emerging",
    "autonomy": "emerging", "genomics": "emerging", "india_growth": "emerging",
    "africa_growth": "emerging", "energy_storage": "emerging", "weight_loss_glp1": "emerging",
    "water_scarcity": "emerging", "bci": "emerging", "nanotechnology": "emerging",
    "carbon_capture": "emerging", "vertical_farming": "emerging", "fusion_energy": "emerging",
    "evtol": "emerging", "fintech_payments": "emerging", "hydrogen": "emerging",
    "crypto_infra": "emerging", "additive_manufacturing": "emerging", "ev_charging": "emerging",
    "legacy_retail": "fading", "ice_autos": "fading",
    "fossil_fuels": "fading", "linear_media": "fading",
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
    "bci": "Neuromodulation and neural-interface medical devices; true BCI pure-plays (Neuralink, Synchron) remain private, so this basket is the nearest liquid public proxy.",
    "nanotechnology": "Nanoscale materials, sensors and particle-delivery systems — a horizontal enabling technology across medicine, electronics and materials rather than one product category.",
    "carbon_capture": "Direct-air-capture and CCS equipment/project developers; still subsidy-dependent and pre-scale, so the basket leans on a diversified major (Oxy's 1PointFive) and equipment suppliers rather than true pure-plays.",
    "vertical_farming": "Indoor/controlled-environment produce growers; the public track record is rough (AppHarvest and Kalera both delisted/bankrupt) — treat as a high-mortality, thesis-not-yet-proven basket, not a settled winner-picking exercise.",
    "fusion_energy": "Commercial fusion power; every true pure-play (Commonwealth Fusion, TAE, Helion) is still private, so this is a single equipment-supplier proxy, not a basket of fusion companies.",
    "evtol": "Electric vertical-takeoff aircraft for urban air mobility; pre-revenue, certification-stage names with heavy cash burn and dilution risk.",
    "fintech_payments": "Secular cash-to-digital payment-rail shift — one of the more mature, cash-generative themes here versus the speculative-growth baskets around it.",
    "hydrogen": "Green/blue hydrogen production, storage and fuel cells; policy- and subsidy-sensitive, thinly profitable across the basket.",
    "crypto_infra": "Exchanges and miners forming the on/off-ramp and infrastructure layer for crypto markets; highly correlated to BTC/crypto price cycles rather than a diversifier.",
    "additive_manufacturing": "Industrial 3D printing for prototyping and end-part production; smaller-cap, lower-conviction theme than most others here.",
    "ev_charging": "Public EV charging network build-out; thin, cash-burning, high-beta names — one of the weaker-conviction themes in this map.",
    "legacy_retail": "Mall-anchor department stores losing share to e-commerce and off-price, structurally.",
    "ice_autos": "Traditional automakers' core internal-combustion business, ceding share to EV-native and Chinese entrants.",
    "fossil_fuels": "Oil & gas majors — still cash-generative today, but on the losing side of a multi-decade energy transition.",
    "linear_media": "Cable/broadcast TV and print, losing both audience and ad dollars to streaming and digital.",
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
    # Nuclear / uranium
    "CCJ": ("nuclear",),
    "UEC": ("nuclear",),
    "LEU": ("nuclear",),
    "SMR": ("nuclear",),
    "OKLO": ("nuclear",),
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
    # Brain-computer interfaces (neuromodulation/neural-interface devices; nearest liquid public proxy)
    "LIVN": ("bci",),
    "NVRO": ("bci",),
    "INSP": ("bci",),
    # Nanotechnology (nanoscale materials, sensors, particle-delivery systems)
    "NNOX": ("nanotechnology",),
    "NVEC": ("nanotechnology",),
    "ARWR": ("nanotechnology",),
    # Carbon capture & sequestration (DAC/CCS equipment + project developers)
    "GTLS": ("carbon_capture", "fusion_energy"),
    "LNZA": ("carbon_capture",),
    # Vertical / controlled-environment farming (rough public track record — see description)
    "LOCL": ("vertical_farming",),
    "VFF": ("vertical_farming",),
    "HYFM": ("vertical_farming",),
    # Fusion energy (GTLS above is the equipment-supplier proxy; no public pure-play exists yet)
    # eVTOL / urban air mobility
    "JOBY": ("evtol",),
    "ACHR": ("evtol",),
    # Digital payments / fintech infrastructure
    "V": ("fintech_payments",),
    "MA": ("fintech_payments",),
    "PYPL": ("fintech_payments",),
    "SQ": ("fintech_payments",),
    # Hydrogen economy (production, storage, fuel cells)
    "PLUG": ("hydrogen",),
    "BLDP": ("hydrogen",),
    "BE": ("hydrogen", "energy_storage"),
    # Crypto / blockchain infrastructure (exchanges + miners)
    "COIN": ("crypto_infra",),
    "MSTR": ("crypto_infra",),
    "MARA": ("crypto_infra",),
    "RIOT": ("crypto_infra",),
    # 3D printing / additive manufacturing
    "DDD": ("additive_manufacturing",),
    "SSYS": ("additive_manufacturing",),
    "PRLB": ("additive_manufacturing",),
    # EV charging infrastructure
    "CHPT": ("ev_charging",),
    "EVGO": ("ev_charging",),
    # Legacy brick-and-mortar retail (fading — mall department stores losing to e-commerce)
    "M": ("legacy_retail",),
    "KSS": ("legacy_retail",),
    "DDS": ("legacy_retail",),
    "GPS": ("legacy_retail",),
    # Internal-combustion automakers (fading — core ICE business, ex their EV/tech optionality)
    "F": ("ice_autos",),
    "GM": ("ice_autos",),
    "STLA": ("ice_autos",),
    # Fossil-fuel majors (fading — long-term energy-transition demand headwind)
    "XOM": ("fossil_fuels",),
    "CVX": ("fossil_fuels",),
    "COP": ("fossil_fuels",),
    "OXY": ("fossil_fuels", "carbon_capture"),
    # Linear TV / print media (fading — audience and ad-dollar share loss to streaming/digital)
    "PARA": ("linear_media",),
    "WBD": ("linear_media",),
    "FOXA": ("linear_media",),
    "NWSA": ("linear_media",),
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
    "XRT": "legacy_retail",
    "CARZ": "ice_autos",
    "XLE": "fossil_fuels", "XOP": "fossil_fuels",
    "PBS": "linear_media",
}


def themes_for(symbol: str) -> list:
    """Curated secular themes for a ticker (empty if unknown)."""
    return list(_THEME_MAP.get(symbol.upper(), ()))


def subsectors_for(theme_key: str) -> dict[str, str] | None:
    """Ticker → subsector-name map for a theme, or None if the theme has no curated split
    (caller then treats each ticker as its own flat unit — see industry_markets.industry_theme_detail)."""
    return _SUBSECTORS.get(theme_key) or None


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
            "lifecycle": THEME_LIFECYCLE.get(key, "emerging"),
            "tickers": tickers,
            "subsectors": subsectors,
            "etfs": sorted(etfs_by_theme.get(key, [])),
        })
    return groups
