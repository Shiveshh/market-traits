import { useEffect, useState } from "react";
import type { GlobalMarkets, IndustryMarkets, MarketWeather } from "./types";

export interface FetchState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

// Same fetch/loading/error shape either app's existing data-fetching convention already expects
// (Business's useJson, Market-Analysis's apiGet+useState) — a plain URL in, {data,loading,error} out.
function useFetchJson<T>(url: string): FetchState<T> {
  const [state, setState] = useState<FetchState<T>>({ data: null, loading: true, error: null });

  useEffect(() => {
    let cancelled = false;
    setState({ data: null, loading: true, error: null });
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`${url} -> HTTP ${r.status}`);
        return r.json();
      })
      .then((data: T) => {
        if (!cancelled) setState({ data, loading: false, error: null });
      })
      .catch((e) => {
        if (!cancelled) setState({ data: null, loading: false, error: String(e) });
      });
    return () => {
      cancelled = true;
    };
  }, [url]);

  return state;
}

export function useMarketWeather(url = "/api/market-weather"): FetchState<MarketWeather> {
  return useFetchJson<MarketWeather>(url);
}

export function useGlobalMarkets(url = "/api/global-markets"): FetchState<GlobalMarkets> {
  return useFetchJson<GlobalMarkets>(url);
}

export function useIndustryMarkets(url = "/api/industry-markets"): FetchState<IndustryMarkets> {
  return useFetchJson<IndustryMarkets>(url);
}
