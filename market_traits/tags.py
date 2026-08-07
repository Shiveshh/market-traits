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
    "precious_metals": "Precious metals / gold & silver miners",
    "steel_aluminum": "Steel & aluminum / reshoring capacity",
    "agri_fertilizer": "Agri-tech / fertilizer & food security",
    "reshoring_industrials": "Reshoring / onshoring industrials",
    "data_privacy_identity": "Data privacy & digital identity",
    "obesity_adjacent_devices": "Obesity-adjacent med-tech & devices",
    "ai_agents_software": "Enterprise AI agents / software",
    "telecom_carriers": "Telecom carriers",
    "insurance": "Insurance",
    "regional_banks": "Regional banks",
    "office_reits": "Office REITs",
    "cannabis": "Cannabis",
    "lab_grown_protein": "Lab-grown / plant-based protein",
    "outdoors_sports": "Outdoor recreation & sporting goods",
    "apparel_fashion": "Apparel & fashion",
    "pc_hardware": "PC hardware / CPU & GPU",
    "home_furnishings": "Home & furnishings",
    "beauty_personal_care": "Beauty & personal care",
    "toys_hobbies": "Toys, games & hobbies",
    "pet_care": "Pet care",
    "travel_leisure": "Travel & leisure",
    "restaurants": "Restaurants & QSR",
    "alcohol_spirits": "Alcohol & spirits",
    "ecommerce_platforms": "E-commerce platforms",
    "mining_diversified": "Diversified & base-metal mining",
    "packaged_food": "Packaged & branded food",
    "beverages": "Non-alcoholic beverages",
    "grocery_retail": "Grocery & food retail",
    "auto_parts": "Cars & auto parts",
    "hvac": "HVAC / air conditioning & heating",
    "gaming": "Video games & interactive entertainment",
    "waste_management": "Waste management & recycling",
    "books_publishing": "Books & publishing",
    "medical_devices": "Medical devices & diagnostics (imaging, hearing aids)",
    "pharmaceuticals": "Pharmaceuticals (broad/generalist)",
    "jewelry": "Jewelry & luxury accessories",
    "airlines": "Airlines",
    "homebuilders": "Homebuilders",
    "tobacco": "Tobacco",
    "office_supplies": "Office & business supplies",
    "chemicals": "Industrial & specialty chemicals",
    "paper_packaging": "Paper & packaging",
    "construction_engineering": "Construction & engineering",
    "utilities_water_gas": "Utilities (water & gas)",
    "reits_diversified": "REITs (residential, industrial, retail)",
    "mass_merchants": "Mass merchants & discount stores",
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
    "precious_metals": "emerging", "steel_aluminum": "emerging", "agri_fertilizer": "emerging",
    "reshoring_industrials": "emerging", "data_privacy_identity": "emerging",
    "obesity_adjacent_devices": "emerging",
    "ai_agents_software": "emerging", "telecom_carriers": "emerging", "insurance": "emerging",
    "regional_banks": "emerging", "office_reits": "emerging", "cannabis": "emerging",
    "lab_grown_protein": "emerging",
    "outdoors_sports": "emerging", "apparel_fashion": "emerging", "pc_hardware": "emerging",
    "home_furnishings": "emerging", "beauty_personal_care": "emerging", "toys_hobbies": "emerging",
    "pet_care": "emerging", "travel_leisure": "emerging", "restaurants": "emerging",
    "alcohol_spirits": "emerging", "ecommerce_platforms": "emerging",
    "mining_diversified": "emerging", "packaged_food": "emerging", "beverages": "emerging",
    "grocery_retail": "emerging", "auto_parts": "emerging", "hvac": "emerging",
    "gaming": "emerging", "waste_management": "emerging", "books_publishing": "emerging",
    "medical_devices": "emerging", "pharmaceuticals": "emerging", "jewelry": "emerging",
    "airlines": "emerging", "homebuilders": "emerging", "tobacco": "emerging",
    "office_supplies": "emerging", "chemicals": "emerging", "paper_packaging": "emerging",
    "construction_engineering": "emerging", "utilities_water_gas": "emerging",
    "reits_diversified": "emerging", "mass_merchants": "emerging",
    "legacy_retail": "fading", "ice_autos": "fading",
    "fossil_fuels": "fading", "linear_media": "fading",
}

# Where each theme sits in the current hype/sentiment cycle (orthogonal to
# THEME_LIFECYCLE's secular emerging/fading axis — this is momentum, not
# direction). One of:
#   "established"  — mature, steady demand, rarely a news-cycle darling
#   "emerging"      — building conviction, not yet broadly chased
#   "hyped"         — currently crowded/frothy, elevated sentiment and multiples
#   "underrated"    — currently out of favor, but the fundamental/secular case still holds —
#                      a mispriced-gem read (e.g. fossil-fuel majors: cash-generative, cheap,
#                      just unloved by ESG-driven flows)
#   "downplayed"    — currently out of favor AND the fundamental case is weak/unproven — no
#                      mispricing thesis, just genuinely out of favor for a reason
# This split matters for sizing: "underrated" is a contrarian-buy candidate, "downplayed" is not.
# This is a point-in-time read (as of 2026-08), not a permanent label — revisit
# periodically as narratives rotate. Every key in THEME_LABELS must appear here.
THEME_HYPE_CYCLE: dict[str, str] = {
    "ai_infra": "hyped", "semiconductors": "hyped", "cybersecurity": "established",
    "electrification": "emerging", "nuclear": "hyped", "biotech_tools": "established",
    "defense_space": "hyped", "healthcare_innov": "established", "robotics": "emerging",
    "quantum_computing": "hyped", "critical_minerals": "emerging", "space_satcom": "emerging",
    "autonomy": "underrated", "genomics": "underrated", "india_growth": "emerging",
    "africa_growth": "emerging", "energy_storage": "established", "weight_loss_glp1": "hyped",
    "water_scarcity": "established", "bci": "emerging", "nanotechnology": "emerging",
    "carbon_capture": "downplayed", "vertical_farming": "downplayed", "fusion_energy": "hyped",
    "evtol": "downplayed", "fintech_payments": "established", "hydrogen": "downplayed",
    "crypto_infra": "hyped", "additive_manufacturing": "underrated", "ev_charging": "downplayed",
    "precious_metals": "hyped", "steel_aluminum": "emerging", "agri_fertilizer": "established",
    "reshoring_industrials": "emerging", "data_privacy_identity": "established",
    "obesity_adjacent_devices": "hyped",
    "ai_agents_software": "hyped", "telecom_carriers": "established", "insurance": "established",
    "regional_banks": "underrated", "office_reits": "downplayed", "cannabis": "downplayed",
    "lab_grown_protein": "downplayed",
    "outdoors_sports": "established", "apparel_fashion": "established", "pc_hardware": "established",
    "home_furnishings": "established", "beauty_personal_care": "established", "toys_hobbies": "established",
    "pet_care": "established", "travel_leisure": "established", "restaurants": "established",
    "alcohol_spirits": "established", "ecommerce_platforms": "hyped",
    "mining_diversified": "established", "packaged_food": "established", "beverages": "established",
    "grocery_retail": "established", "auto_parts": "established", "hvac": "established",
    "gaming": "established", "waste_management": "established", "books_publishing": "downplayed",
    "medical_devices": "established", "pharmaceuticals": "established", "jewelry": "established",
    "airlines": "downplayed", "homebuilders": "underrated", "tobacco": "underrated",
    "office_supplies": "downplayed", "chemicals": "established", "paper_packaging": "downplayed",
    "construction_engineering": "established", "utilities_water_gas": "established",
    "reits_diversified": "established", "mass_merchants": "established",
    "legacy_retail": "downplayed", "ice_autos": "downplayed",
    "fossil_fuels": "underrated", "linear_media": "downplayed",
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
    "critical_minerals": "The supply-chain bottleneck shared by EVs, robotics, nuclear and defense: lithium, rare-earth magnets, copper, and polysilicon.",
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
    "precious_metals": "Gold/silver miners as an inflation and currency-debasement hedge, distinct from critical_minerals' industrial-demand framing.",
    "steel_aluminum": "Domestic steel and aluminum capacity benefiting from tariffs, reshoring and infrastructure spend.",
    "agri_fertilizer": "Potash/nitrogen fertilizer and farm inputs — food-security demand independent of any one crop cycle; complements vertical_farming.",
    "reshoring_industrials": "Broader supply-chain-resilience trade — industrial capacity moving onshore/nearshore beyond any single metal or material.",
    "data_privacy_identity": "Identity verification, consent and data-governance compliance spend, adjacent to but distinct from cybersecurity's attack-surface thesis.",
    "obesity_adjacent_devices": "Bariatric surgery, continuous glucose monitoring and metabolic-health devices riding the same demand wave as GLP-1 drugs without drug-pricing risk.",
    "ai_agents_software": "Enterprise software layer (agents, copilots, workflow automation) monetizing the AI buildout on the applications side, distinct from ai_infra's hardware/hyperscale layer.",
    "telecom_carriers": "Mature, capital-intensive wireless/broadband carriers — steady cash generation, low growth, rarely a hype-cycle name.",
    "insurance": "Property & casualty and life insurers — mature, rate-cycle-driven, defensive earnings base.",
    "regional_banks": "Regional/mid-size US banks — deposit-funded lenders exposed to net-interest-margin and credit-cycle swings, currently out of favor post-2023 deposit-flight stress.",
    "office_reits": "Commercial office landlords — structurally impaired by remote/hybrid work, currently the most out-of-favor real-estate subsector.",
    "cannabis": "US cannabis operators — hyped 2018-2021 on legalization optimism, now down hard on stalled federal reform and oversupply.",
    "lab_grown_protein": "Plant-based and cultivated-meat producers — hyped 2019-2021 IPO wave, now down sharply on weak unit economics and demand that never materialized at scale.",
    "legacy_retail": "Mall-anchor department stores losing share to e-commerce and off-price, structurally.",
    "ice_autos": "Traditional automakers' core internal-combustion business, ceding share to EV-native and Chinese entrants.",
    "fossil_fuels": "Oil & gas majors — still cash-generative today, but on the losing side of a multi-decade energy transition.",
    "linear_media": "Cable/broadcast TV and print, losing both audience and ad dollars to streaming and digital.",
    "outdoors_sports": "Outdoor recreation, sporting goods and activity-specific gear (scuba, skiing, camping, team sports) — discretionary spend tied to household income and leisure time.",
    "apparel_fashion": "Clothing, footwear and accessories brands and retailers — cyclical, trend-driven consumer discretionary demand.",
    "pc_hardware": "Personal-computing hardware — CPUs, GPUs, and the OEM/component makers around them; overlaps semiconductors but framed around the PC/gaming build cycle rather than datacenter AI capex.",
    "home_furnishings": "Furniture, home decor and home-improvement retail — big-ticket discretionary spend tied to housing turnover.",
    "beauty_personal_care": "Cosmetics, skincare and personal-care brands/retailers — resilient, brand-loyalty-driven consumer staple-ish demand.",
    "toys_hobbies": "Toys, games and hobbyist products — seasonal, IP-and-licensing-driven consumer demand.",
    "pet_care": "Pet food, veterinary care and pet-specialty retail — a structurally growing, historically recession-resistant consumer category.",
    "travel_leisure": "Airlines, cruise lines and travel-booking platforms — highly cyclical, fuel- and consumer-confidence-sensitive discretionary spend.",
    "restaurants": "Fast-casual, QSR and dining chains — traffic- and labor-cost-sensitive consumer discretionary demand.",
    "alcohol_spirits": "Beer, wine and spirits producers/distributors — a classically defensive consumer-staples subsector.",
    "ecommerce_platforms": "Online-retail and marketplace platforms — the distribution layer across every physical-goods category above, distinct from any one product vertical.",
    "mining_diversified": "Diversified and base-metal miners (iron ore, coal, copper) — commodity-price-cyclical, distinct from critical_minerals' EV/battery-supply-chain framing and precious_metals' inflation-hedge framing.",
    "packaged_food": "Branded packaged and processed food producers — defensive consumer-staples demand, largely insulated from discretionary spending swings.",
    "beverages": "Non-alcoholic beverage producers (soda, coffee, energy drinks) — brand-loyalty-driven consumer-staples demand, distinct from alcohol_spirits.",
    "grocery_retail": "Supermarket and food-retail chains — thin-margin, high-volume defensive retail distinct from the packaged_food producers that supply them.",
    "auto_parts": "Auto-parts retailers and suppliers — aftermarket/repair demand is non-cyclical (cars need maintenance regardless of new-car sales), distinct from ice_autos' new-vehicle-sales exposure.",
    "hvac": "HVAC, air-conditioning and heating equipment makers — structural demand tailwind from rising global temperatures and data-center cooling buildout.",
    "gaming": "Video-game publishers, platforms and hardware — hit-driven content cycles plus recurring live-service/subscription revenue.",
    "waste_management": "Waste collection, disposal and recycling — highly regulated, contracted, recession-resistant municipal/industrial demand.",
    "books_publishing": "Book publishers and booksellers — a small, structurally mature category with thin public pure-play coverage.",
    "medical_devices": "Diagnostic imaging, hearing aids and other medical-device makers — recurring, demographically-driven demand distinct from healthcare_innov's novel-modality framing.",
    "pharmaceuticals": "Large-cap generalist pharmaceutical makers — broad drug-portfolio exposure, distinct from healthcare_innov's novel-modality and weight_loss_glp1's single-category framing.",
    "jewelry": "Jewelry, watch and luxury-accessory makers/retailers — brand-power-driven discretionary spend, distinct from apparel_fashion's clothing/footwear framing.",
    "airlines": "Passenger airlines — highly cyclical, fuel- and labor-cost-sensitive, thin margins; split out of travel_leisure's broader booking/hotel/cruise mix.",
    "homebuilders": "New-home construction companies — housing-start and mortgage-rate sensitive, distinct from home_furnishings' furnish-the-house-after-purchase framing.",
    "tobacco": "Cigarette and tobacco-alternative makers — high-margin, high-cash-generative defensive staple with structural volume decline offset by pricing power.",
    "office_supplies": "Office and business-supply retailers/distributors — a thin, structurally mature category pressured by remote work and e-commerce.",
    "chemicals": "Industrial and specialty chemical producers — broad input-cost/cycle exposure across plastics, coatings and materials, distinct from agri_fertilizer's farm-input focus.",
    "paper_packaging": "Paper, containerboard and packaging producers — e-commerce-driven shipping demand offset by structural print/paper decline.",
    "construction_engineering": "Non-residential construction, engineering and infrastructure contractors — project-backlog-driven, benefits from public infrastructure spend, distinct from reshoring_industrials' broader onshoring-capacity framing.",
    "utilities_water_gas": "Regulated water and natural-gas utilities — a defensive, rate-base-driven yield basket, distinct from electrification's growth-capex framing.",
    "reits_diversified": "Residential, industrial/logistics and retail REITs — landlord exposure to sub-sectors other than the structurally-impaired office_reits.",
    "mass_merchants": "Big-box and discount mass merchants (Walmart/Target-style) — broad-basket general merchandise retail, distinct from grocery_retail's food focus and legacy_retail's structurally-declining mall-anchor department stores.",
}

# Curated ticker → themes. Deliberately conservative; extend as conviction warrants.
_THEME_MAP: dict[str, tuple[str, ...]] = {
    # AI infrastructure (compute, accelerators, networking, hyperscale)
    "NVDA": ("ai_infra", "semiconductors", "pc_hardware"),
    "AMD": ("ai_infra", "semiconductors", "pc_hardware"),
    "AVGO": ("ai_infra", "semiconductors"),
    "MRVL": ("ai_infra", "semiconductors"),
    "SMCI": ("ai_infra",),
    "DELL": ("ai_infra",),
    "ANET": ("ai_infra",),
    "MSFT": ("ai_infra",),
    "GOOGL": ("ai_infra",),
    "AMZN": ("ai_infra", "ecommerce_platforms"),
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
    "PWR": ("electrification", "construction_engineering"),
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
    "SCCO": ("critical_minerals",),
    "TECK": ("critical_minerals",),
    "USAR": ("critical_minerals",),
    "DQ": ("critical_minerals",),
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
    "AWK": ("water_scarcity", "utilities_water_gas"),
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
    # Precious metals / gold & silver miners (inflation hedge, distinct from critical_minerals)
    "NEM": ("precious_metals",),
    "GOLD": ("precious_metals",),
    "AEM": ("precious_metals",),
    "PAAS": ("precious_metals",),
    "WPM": ("precious_metals",),
    "KGC": ("precious_metals",),
    # Steel & aluminum / reshoring capacity
    "NUE": ("steel_aluminum",),
    "STLD": ("steel_aluminum",),
    "CLF": ("steel_aluminum",),
    "X": ("steel_aluminum",),
    "CENX": ("steel_aluminum",),
    # Agri-tech / fertilizer & food security
    "MOS": ("agri_fertilizer",),
    "CF": ("agri_fertilizer",),
    "NTR": ("agri_fertilizer",),
    "ICL": ("agri_fertilizer",),
    "DE": ("agri_fertilizer",),
    # Reshoring / onshoring industrials (broader supply-chain-resilience trade)
    "CAT": ("reshoring_industrials",),
    "EMR": ("reshoring_industrials",),
    "HON": ("reshoring_industrials",),
    "ITW": ("reshoring_industrials",),
    "GE": ("reshoring_industrials",),
    # Data privacy & digital identity (adjacent to, distinct from, cybersecurity)
    "OKTA": ("data_privacy_identity",),
    "PING": ("data_privacy_identity",),
    "ONTF": ("data_privacy_identity",),
    "TWLO": ("data_privacy_identity",),
    # Obesity-adjacent med-tech & devices (companion to weight_loss_glp1, non-drug)
    "PODD": ("obesity_adjacent_devices",),
    "DXCM": ("obesity_adjacent_devices",),
    "INMD": ("obesity_adjacent_devices",),
    "IRTC": ("obesity_adjacent_devices",),
    # Enterprise AI agents / software (applications layer, distinct from ai_infra hardware)
    "AI": ("ai_agents_software",),
    "NOW": ("ai_agents_software",),
    "CRM": ("ai_agents_software",),
    "SNOW": ("ai_agents_software",),
    # Telecom carriers (mature, capital-intensive wireless/broadband)
    "T": ("telecom_carriers",),
    "VZ": ("telecom_carriers",),
    "TMUS": ("telecom_carriers",),
    # Insurance (P&C and life, mature/defensive)
    "TRV": ("insurance",),
    "ALL": ("insurance",),
    "PGR": ("insurance",),
    "CB": ("insurance",),
    # Regional banks (currently out of favor)
    "ZION": ("regional_banks",),
    "CMA": ("regional_banks",),
    "KEY": ("regional_banks",),
    "FITB": ("regional_banks",),
    # Office REITs (currently the most out-of-favor real-estate subsector)
    "BXP": ("office_reits",),
    "VNO": ("office_reits",),
    "SLG": ("office_reits",),
    # Cannabis (hyped 2018-2021, down since)
    "TLRY": ("cannabis",),
    "CGC": ("cannabis",),
    "CRON": ("cannabis",),
    # Lab-grown / plant-based protein (hyped 2019-2021, down since)
    "BYND": ("lab_grown_protein",),
    "OTLY": ("lab_grown_protein",),
    "STKL": ("lab_grown_protein",),
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
    # Outdoor recreation & sporting goods (scuba, skiing, camping, team sports)
    "DKS": ("outdoors_sports",),
    "YETI": ("outdoors_sports",),
    "JOUT": ("outdoors_sports",),
    "MCFT": ("outdoors_sports",),
    "PII": ("outdoors_sports",),
    "COLM": ("outdoors_sports", "apparel_fashion"),
    "VIST": ("outdoors_sports",),
    # Apparel & fashion (clothing, footwear, accessories)
    "NKE": ("apparel_fashion", "outdoors_sports"),
    "DECK": ("apparel_fashion", "outdoors_sports"),
    "LULU": ("apparel_fashion", "outdoors_sports"),
    "ONON": ("apparel_fashion", "outdoors_sports"),
    "RL": ("apparel_fashion",),
    "TPR": ("apparel_fashion",),
    "VFC": ("apparel_fashion", "outdoors_sports"),
    "CRI": ("apparel_fashion",),
    "SKX": ("apparel_fashion",),
    "PVH": ("apparel_fashion",),
    # PC hardware / CPU & GPU (build-cycle framing, distinct from datacenter AI capex)
    "INTC": ("pc_hardware", "semiconductors"),
    "HPQ": ("pc_hardware",),
    "LOGI": ("pc_hardware",),
    "CRSR": ("pc_hardware",),
    "STX": ("pc_hardware",),
    "WDC": ("pc_hardware",),
    # Home & furnishings (furniture, decor, home-improvement retail)
    "HD": ("home_furnishings",),
    "LOW": ("home_furnishings",),
    "W": ("home_furnishings",),
    "RH": ("home_furnishings",),
    "WSM": ("home_furnishings",),
    "TPX": ("home_furnishings",),
    # Beauty & personal care (cosmetics, skincare, personal care)
    "EL": ("beauty_personal_care",),
    "ELF": ("beauty_personal_care",),
    "ULTA": ("beauty_personal_care",),
    "COTY": ("beauty_personal_care",),
    "IPAR": ("beauty_personal_care",),
    # Toys, games & hobbies
    "HAS": ("toys_hobbies",),
    "MAT": ("toys_hobbies",),
    "FNKO": ("toys_hobbies",),
    "JAKK": ("toys_hobbies",),
    # Pet care (food, vet, pet-specialty retail)
    "CHWY": ("pet_care",),
    "FRPT": ("pet_care",),
    "IDXX": ("pet_care",),
    "WOOF": ("pet_care",),
    # Travel & leisure (airlines, cruise lines, booking platforms)
    "BKNG": ("travel_leisure",),
    "ABNB": ("travel_leisure",),
    "RCL": ("travel_leisure",),
    "CCL": ("travel_leisure",),
    "DAL": ("travel_leisure", "airlines"),
    "MAR": ("travel_leisure",),
    "EXPE": ("travel_leisure",),
    # Restaurants & QSR (fast-casual, dining chains)
    "MCD": ("restaurants",),
    "SBUX": ("restaurants",),
    "CMG": ("restaurants",),
    "YUM": ("restaurants",),
    "DPZ": ("restaurants",),
    "DASH": ("restaurants",),
    # Alcohol & spirits (beer, wine, spirits)
    "STZ": ("alcohol_spirits",),
    "BF-B": ("alcohol_spirits",),
    "DEO": ("alcohol_spirits",),
    "TAP": ("alcohol_spirits",),
    # E-commerce platforms (distribution layer, distinct from any one product vertical; AMZN tagged above)
    "SHOP": ("ecommerce_platforms",),
    "ETSY": ("ecommerce_platforms",),
    "MELI": ("ecommerce_platforms",),
    "BABA": ("ecommerce_platforms",),
    # Diversified & base-metal mining (commodity-price-cyclical; SCCO/FCX/TECK already tagged under critical_minerals)
    "BHP": ("mining_diversified",),
    "RIO": ("mining_diversified",),
    "VALE": ("mining_diversified",),
    "BTU": ("mining_diversified",),
    "AA": ("mining_diversified",),
    # Packaged & branded food (defensive consumer staples)
    "KHC": ("packaged_food",),
    "GIS": ("packaged_food",),
    "K": ("packaged_food",),
    "HSY": ("packaged_food",),
    "MDLZ": ("packaged_food",),
    "CAG": ("packaged_food",),
    "CPB": ("packaged_food",),
    # Non-alcoholic beverages (brand-loyalty consumer staples)
    "KO": ("beverages",),
    "PEP": ("beverages",),
    "KDP": ("beverages",),
    "MNST": ("beverages",),
    "CELH": ("beverages",),
    # Grocery & food retail (thin-margin, high-volume defensive retail)
    "KR": ("grocery_retail",),
    "ACI": ("grocery_retail",),
    "SFM": ("grocery_retail",),
    "COST": ("grocery_retail", "mass_merchants"),
    # Cars & auto parts (aftermarket/repair, non-cyclical vs. new-vehicle sales)
    "AZO": ("auto_parts",),
    "ORLY": ("auto_parts",),
    "AAP": ("auto_parts",),
    "APTV": ("auto_parts",),
    "BWA": ("auto_parts",),
    "LKQ": ("auto_parts",),
    # HVAC / air conditioning & heating (structural demand tailwind)
    "CARR": ("hvac",),
    "TT": ("hvac",),
    "LII": ("hvac",),
    "JCI": ("hvac",),
    # Video games & interactive entertainment
    "EA": ("gaming",),
    "TTWO": ("gaming",),
    "RBLX": ("gaming",),
    "NTDOY": ("gaming",),
    # Waste management & recycling
    "WM": ("waste_management",),
    "RSG": ("waste_management",),
    "WCN": ("waste_management",),
    "CLH": ("waste_management",),
    # Books & publishing (thin public pure-play coverage)
    "SCHL": ("books_publishing",),
    "NWS": ("books_publishing", "linear_media"),
    # Medical devices & diagnostics (imaging, hearing aids)
    "MDT": ("medical_devices",),
    "SYK": ("medical_devices",),
    "BSX": ("medical_devices",),
    "GEHC": ("medical_devices",),
    "HOLX": ("medical_devices",),
    "RMD": ("medical_devices",),
    "COO": ("medical_devices",),
    # Pharmaceuticals (broad/generalist; LLY/NVO/VRTX/REGN/AMGN already tagged under healthcare_innov/weight_loss_glp1)
    "PFE": ("pharmaceuticals",),
    "MRK": ("pharmaceuticals",),
    "JNJ": ("pharmaceuticals",),
    "BMY": ("pharmaceuticals",),
    "GILD": ("pharmaceuticals",),
    "AZN": ("pharmaceuticals",),
    "SNY": ("pharmaceuticals",),
    "NVS": ("pharmaceuticals",),
    # Jewelry & luxury accessories
    "SIG": ("jewelry",),
    "MOV": ("jewelry",),
    "CPRI": ("jewelry", "apparel_fashion"),
    # Airlines (split out of travel_leisure; DAL already tagged travel_leisure+airlines above)
    "UAL": ("airlines",),
    "LUV": ("airlines",),
    "AAL": ("airlines",),
    "ALK": ("airlines",),
    # Homebuilders (new-home construction, distinct from home_furnishings)
    "DHI": ("homebuilders",),
    "LEN": ("homebuilders",),
    "PHM": ("homebuilders",),
    "NVR": ("homebuilders",),
    "TOL": ("homebuilders",),
    # Tobacco (high-margin defensive staple)
    "MO": ("tobacco",),
    "PM": ("tobacco",),
    "BTI": ("tobacco",),
    # Office & business supplies
    "ODP": ("office_supplies",),
    "SPB": ("office_supplies",),
    # Industrial & specialty chemicals
    "LIN": ("chemicals",),
    "APD": ("chemicals",),
    "DD": ("chemicals",),
    "DOW": ("chemicals",),
    "LYB": ("chemicals",),
    "PPG": ("chemicals",),
    "ECL": ("chemicals",),
    # Paper & packaging
    "IP": ("paper_packaging",),
    "PKG": ("paper_packaging",),
    "WRK": ("paper_packaging",),
    "SEE": ("paper_packaging",),
    "AMCR": ("paper_packaging",),
    # Construction & engineering (project-backlog-driven, infrastructure spend; PWR tagged above)
    "ACM": ("construction_engineering",),
    "J": ("construction_engineering",),
    "FLR": ("construction_engineering",),
    "MTZ": ("construction_engineering",),
    # Utilities (water & gas) — defensive rate-base yield, distinct from electrification's growth framing; AWK tagged above
    "WTRG": ("utilities_water_gas",),
    "ATO": ("utilities_water_gas",),
    "NI": ("utilities_water_gas",),
    "SO": ("utilities_water_gas",),
    # REITs (residential, industrial/logistics, retail — beyond office_reits)
    "PLD": ("reits_diversified",),
    "AVB": ("reits_diversified",),
    "EQR": ("reits_diversified",),
    "O": ("reits_diversified",),
    "SPG": ("reits_diversified",),
    "EXR": ("reits_diversified",),
    # Mass merchants & discount stores
    "WMT": ("mass_merchants",),
    "TGT": ("mass_merchants",),
    "DG": ("mass_merchants",),
    "DLTR": ("mass_merchants",),
    "BJ": ("mass_merchants",),
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
        "MP": "Rare earths", "USAR": "Rare-earth magnets",
        "FCX": "Copper", "SCCO": "Copper", "TECK": "Copper",
        "DQ": "Polysilicon",
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
    "GDX": "precious_metals", "GDXJ": "precious_metals", "SIL": "precious_metals",
    "SLX": "steel_aluminum",
    "MOO": "agri_fertilizer", "SOIL": "agri_fertilizer",
    "PAVE": "reshoring_industrials",
    "IGV": "ai_agents_software",
    "IYZ": "telecom_carriers", "VOX": "telecom_carriers",
    "KIE": "insurance", "IAK": "insurance",
    "KRE": "regional_banks", "IAT": "regional_banks",
    "MJ": "cannabis", "MSOS": "cannabis",
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
            "hype_cycle": THEME_HYPE_CYCLE.get(key, "emerging"),
            "tickers": tickers,
            "subsectors": subsectors,
            "etfs": sorted(etfs_by_theme.get(key, [])),
        })
    return groups
