# Changelog

## 0.5.6

- Add optional Alpha Vantage corporate events for upcoming earnings, dividend date and ex-dividend date.
- Show corporate event source and unavailable-state notes in each ticker card.
- Keep corporate events non-blocking when the Alpha Vantage API key is missing or a provider call fails.

## 0.5.5

- Add Alpha Vantage quote, history and symbol search integration when an API key is configured.
- Add market data provider fallback logic so Yahoo can be used when Alpha Vantage is unavailable or rate-limited.
- Keep provider source labels visible in the dashboard data audit.

## 0.5.4

- Add configurable market data provider options in the add-on configuration.
- Add Alpha Vantage API key field for the next provider integration step.
- Add fallback provider option for future source comparison and reliability checks.

## 0.5.3

- Add per-ticker data audit details for source troubleshooting.
- Show effective range, point count, first/last close and percentage calculation formula.

## 0.5.2

- Show only the selected chart range percentage in ticker cards.
- Remove the separate daily percentage metric to avoid mixing `1D`, `1M`, `1Y` and total views.

## 0.5.1

- Add add-on-local changelog so Home Assistant users can inspect release notes from the add-on package.
- Document that both repository and add-on changelogs must be updated for every release.

## 0.5.0

- Add EUR/USD price handling for quotes and chart history.
- Show both EUR and USD values in the price card.
- Add a EUR/USD chart currency switch.
- Fetch Yahoo Finance EUR/USD exchange rate and show it in chart metadata.

## 0.4.3

- Improve mobile responsiveness and remove horizontal overflow on narrow screens.
- Make range buttons wrap into a compact grid on mobile instead of scrolling sideways.
- Adjust ticker cards, chart metadata, metrics and news rows for small screens.

## 0.4.2

- Harden the add-on security profile for Raspberry Pi deployments.
- Restrict supported architectures to Raspberry Pi-oriented `aarch64` and `armv7`.
- Run the application as a non-root user inside the container.
- Explicitly declare no host network, host namespaces, Docker API, Supervisor API, Home Assistant API, auth API, privileged capabilities or full access.
- Enable tmpfs for temporary files.
- Publish prebuilt per-architecture GHCR images and sign them with Cosign from GitHub Actions.

## 0.4.1

- Show when financial data was fetched and link to the Yahoo Finance source page for each ticker.
- Add range-specific performance metrics so the description changes when switching chart range.
- Force fresh overview requests when changing range to avoid stale chart data in the browser or Ingress panel.
- Add explicit range trend text to every ticker card.

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
