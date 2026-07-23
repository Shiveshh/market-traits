# market-traits-frontend

Shared React data hooks + TypeScript types for the [market-traits](../README.md) Python package's
API responses. Hooks and types only — no UI components, since consuming apps use different design
systems and should style the data themselves.

## Install

```
npm install github:Shiveshh/market-traits#main --workspace-root=frontend
```

or, in `package.json`:

```json
"dependencies": {
  "market-traits-frontend": "github:Shiveshh/market-traits#main:frontend"
}
```

`npm install` runs the package's `prepare` script automatically for git dependencies, which
compiles `src/` to `dist/` — no manual build step needed in the consuming repo.

## Usage

```tsx
import { useMarketWeather, useGlobalMarkets, useIndustryMarkets } from "market-traits-frontend";

function MyMarketWeatherTab() {
  const { data, loading, error } = useMarketWeather(); // defaults to fetch("/api/market-weather")
  if (loading) return <Spinner />;
  if (error || !data) return <ErrorBox error={error} />;
  return <div>{data.regime} — score {data.score}</div>;
}
```

Each hook accepts an optional URL override (default assumes same-origin `/api/...`):

```tsx
useMarketWeather("https://other-host/api/market-weather");
```

Types (`MarketWeather`, `GlobalMarkets`, `IndustryMarkets`, `Country`, `Industry`, ...) are exported
for building your own presentational components around the data.

## Keeping consumers in sync

Edit `src/`, commit, push. Each consuming repo picks up the change with:

```
npm install -U github:Shiveshh/market-traits#main:frontend
```
