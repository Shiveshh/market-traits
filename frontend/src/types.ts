// Mirrors the JSON shapes returned by the market-traits Python package
// (market_weather(), global_markets(), industry_markets()).

export interface WeatherComponents {
  trend: number;
  breadth: number;
  efficiency: number;
  calm: number;
  risk_appetite: number;
}

export interface MarketWeather {
  as_of: string;
  score: number;
  regime: string;
  regime_code: string;
  for_book: string;
  components: WeatherComponents;
  past: { dates: string[]; scores: number[] };
  forecast: { read: string; score_20d_change: number; confidence: string };
  note: string;
  error?: string;
}

export interface PastPhasePoint {
  month: string;
  phase: string;
}

export interface SeasonMonth {
  month: number;
  label: string;
  avg_pct: number | null;
  t: number | null;
  n: number;
  band: string;
  color: string;
}

export interface SeasonBand {
  label: string;
  color: string;
}

export interface Phase {
  label: string;
  rank: number;
  color: string;
}

export interface Country {
  iso: string;
  iso_num?: string | null;
  country: string;
  etf: string;
  index_cfd: string | null;
  tradeable: boolean;
  row: number;
  col: number;
  phase: string;
  color: string;
  mom6_pct?: number;
  mom1_pct?: number;
  efficiency?: number;
  above_200d?: boolean;
  forward_lean?: string;
  accel?: number;
  rel_strength?: number;
  past?: PastPhasePoint[];
  pe_ratio?: number | null;
  valuation_pctile?: number;
  valuation_label?: string;
  seasonality?: SeasonMonth[];
}

export interface CountryLeader {
  country: string;
  phase: string;
  mom6_pct: number;
  tradeable?: boolean;
  index_cfd?: string | null;
}

export interface GlobalMarkets {
  as_of: string;
  countries: Country[];
  phases: Record<string, Phase>;
  season_scale: Record<string, SeasonBand>;
  leaders: CountryLeader[];
  laggards: CountryLeader[];
  note: string;
  error?: string;
}

export interface Geography {
  country: string;
  n: number;
}

export interface Valuation {
  n: number;
  verdict: string;
  mean_margin_of_safety_pct?: number | null;
}

export interface Industry {
  key: string;
  label: string;
  description: string;
  etf: string | null;
  etfs: string[];
  tickers: string[];
  geography: Geography[];
  valuation: Valuation;
  phase: string;
  color: string;
  mom6_pct?: number;
  mom1_pct?: number;
  efficiency?: number;
  above_200d?: boolean;
  forward_lean?: string;
  accel?: number;
  rel_strength?: number;
  past?: PastPhasePoint[];
  seasonality?: SeasonMonth[];
}

export interface IndustryLeader {
  label: string;
  phase: string;
  mom6_pct: number;
}

export interface IndustryMarkets {
  as_of: string;
  industries: Industry[];
  phases: Record<string, Phase>;
  season_scale: Record<string, SeasonBand>;
  leaders: IndustryLeader[];
  laggards: IndustryLeader[];
  note: string;
  error?: string;
}
