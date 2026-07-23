# market-traits-frontend

Shared React data hooks + TypeScript types for the [market-traits](../README.md) Python package's
API responses. Hooks and types only — no UI components, since consuming apps use different design
systems and should style the data themselves.

The npm package lives here for organization, but its `package.json`/`tsconfig.json` sit at the repo
root (`../package.json`) — plain `npm install git+...` only works when `package.json` is at the git
repo root, so that's where it has to be. `market_traits/` (the Python package) is unaffected; pip and
npm each ignore the other's config file.

## Install

```
npm install github:Shiveshh/market-traits#main
```

or, in `package.json`:

```json
"dependencies": {
  "market-traits-frontend": "github:Shiveshh/market-traits#main"
}
```

`npm install` runs the package's `prepare` script automatically for git dependencies, which
compiles `frontend/src/` to `frontend/dist/` — no manual build step needed in the consuming repo.

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

Edit `frontend/src/`, commit, push. Each consuming repo picks up the change with:

```
npm install -U github:Shiveshh/market-traits#main
```
