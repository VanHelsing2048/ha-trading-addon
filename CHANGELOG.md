# Changelog

## 0.4.0

- Replace the generic chart selector with trading-style range buttons: today, 1 week, 1 month, 1 year and total.
- Fetch Yahoo Finance history with range-specific intervals instead of reusing daily data for every view.
- Show chart source, selected range and covered dates on every ticker card.
- Add price scale labels and date labels directly on charts.
- Add per-ticker news sections with source and openable links.

## 0.3.0

- Add live symbol search/autocomplete while typing a ticker.
- Add Yahoo Finance-backed quote and historical price provider.
- Make live market data the default mode for new installs.
- Stop drawing invented chart data in live mode when the remote provider is unavailable.
- Show unavailable market data explicitly instead of silently presenting demo history.

## 0.2.3

- Improve Home Assistant security profile by removing the unused host port mapping.
- Store the SQLite database in the add-on's private `/data` volume instead of requesting `addon_config:rw`.
- Explicitly keep the Ingress panel admin-only.

## 0.2.2

- Remove deprecated `build.yaml` and move architecture selection into the Dockerfile.
- Build from the Home Assistant Python base image matching `BUILD_ARCH`, fixing Raspberry Pi 4/aarch64 installs.
- Add Home Assistant image labels directly in the Dockerfile.
- Use plain `uvicorn` instead of `uvicorn[standard]` to reduce native dependency load on Raspberry Pi.

## 0.2.1

- Fix Docker build on non-amd64 Home Assistant hosts by adding architecture-specific base images.
- Stop defaulting the Dockerfile to the amd64 base image.

## 0.2.0

- Add configurable dashboard controls for ticker, name, sector and watchlist filtering.
- Add 30/90/180/365 day price trend charts for every tracked symbol.
- Add overview API with ticker metadata, signal and history in one response.
- Add historical price API ready for real market-data providers.
- Add Home Assistant add-on icon.

## 0.1.0

- Initial Home Assistant add-on repository.
- Add FastAPI backend, SQLite watchlist, demo quotes, RSS news search and signal scoring.
- Add web dashboard served through Home Assistant Ingress.
