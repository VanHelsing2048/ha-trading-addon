const signalsEl = document.querySelector("#signals");
const newsEl = document.querySelector("#news");
const form = document.querySelector("#ticker-form");
const refreshButton = document.querySelector("#refresh");
const searchButton = document.querySelector("#search-news");
const queryInput = document.querySelector("#news-query");
const filterInput = document.querySelector("#watchlist-filter");
const rangeTabs = document.querySelector("#range-tabs");
const currencyTabs = document.querySelector("#currency-tabs");
const summaryEl = document.querySelector("#summary");
const symbolInput = document.querySelector("#symbol");
const nameInput = document.querySelector("#name");
const sectorInput = document.querySelector("#sector");
const symbolOptions = document.querySelector("#symbol-options");
const suggestionsEl = document.querySelector("#symbol-suggestions");

let overviewState = [];
let symbolResults = [];
let suggestTimer;
let activeRange = "1M";
let activeCurrency = "EUR";

async function request(path, options) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

function formatVolume(value) {
  return Intl.NumberFormat("it-IT", { notation: "compact" }).format(value);
}

function formatPrice(value) {
  return Intl.NumberFormat("it-IT", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(value);
}

function formatMoney(value, currency) {
  if (value === null || value === undefined) return "n/d";
  return Intl.NumberFormat("it-IT", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value) {
  if (value === null || value === undefined) return "n/d";
  return `${value >= 0 ? "+" : ""}${formatPrice(value)}%`;
}

function formatDateTime(value) {
  if (!value) return "n/d";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatDate(value) {
  if (!value) return "n/d";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(date);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function signalCard(signal) {
  const safeSymbol = escapeHtml(signal.symbol);
  const safeSource = escapeHtml(signal.quote.source);
  return `
    <article class="signal">
      <header>
        <div>
          <div class="symbol">${safeSymbol}</div>
          <div class="muted">${safeSource}</div>
        </div>
        <span class="stance ${escapeHtml(signal.stance)}">${escapeHtml(signal.stance)}</span>
      </header>
      <div class="metric-row">
        <div class="metric"><span class="muted">Prezzo</span><strong>${signal.quote.price}</strong></div>
        <div class="metric"><span class="muted">Score</span><strong>${signal.score}</strong></div>
      </div>
      <div class="metric"><span class="muted">Volume</span><strong>${formatVolume(signal.quote.volume)}</strong></div>
      <ul class="reasons">${signal.reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul>
      <button class="remove" data-symbol="${safeSymbol}" type="button">Rimuovi</button>
    </article>
  `;
}

function insightCard(item) {
  const { ticker, signal, history, chart_source: chartSource, chart_range: chartRange } = item;
  const rangeClass = (item.range_change_percent || 0) >= 0 ? "Bullish" : "Bearish";
  const subtitle = [ticker.name, ticker.sector].filter(Boolean).map(escapeHtml).join(" - ");
  const historyJson = escapeHtml(JSON.stringify(history));
  const sourceUrl = item.chart_source_url || signal.quote.source_url || "";
  const sourceLabel = sourceName(chartSource || signal.quote.source);
  const sourceLink = sourceUrl
    ? `<a class="source-link" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">${escapeHtml(sourceLabel)}</a>`
    : escapeHtml(sourceLabel);
  const sourceMeta = `${rangeLabel(chartRange || activeRange)} - aggiornato ${formatDateTime(item.chart_as_of || signal.quote.as_of)}`;
  const fxMeta = signal.quote.eur_usd_rate ? `Cambio EUR/USD ${signal.quote.eur_usd_rate}` : "Cambio EUR/USD n/d";
  const relatedNews = signal.news?.length ? signal.news.slice(0, 3).map(newsItemCompact).join("") : `<p class="muted small">Nessuna notizia collegata.</p>`;
  const auditRows = [
    ["Range", chartRange || activeRange],
    ["Punti", item.history_points ?? history.length],
    ["Primo close", item.first_close === null || item.first_close === undefined ? "n/d" : `${signal.quote.currency} ${formatPrice(item.first_close)}`],
    ["Ultimo close", item.last_close === null || item.last_close === undefined ? "n/d" : `${signal.quote.currency} ${formatPrice(item.last_close)}`],
    ["Calcolo", item.calculation_note || "n/d"],
  ];
  const chartMarkup = history.length
    ? `<canvas class="chart" width="640" height="260" data-history="${historyJson}" data-range="${escapeHtml(chartRange || activeRange)}" aria-label="Andamento ${escapeHtml(ticker.symbol)}"></canvas>`
    : `<div class="chart chart-empty">Storico reale non disponibile</div>`;
  return `
    <article class="signal insight-card">
      <header>
        <div>
          <div class="symbol">${escapeHtml(ticker.symbol)}</div>
          <div class="muted">${subtitle || "Titolo monitorato"}</div>
        </div>
        <span class="stance ${escapeHtml(signal.stance)}">${escapeHtml(signal.stance)}</span>
      </header>
      <div class="chart-meta">
        <span>${sourceLink}</span>
        <span>${escapeHtml(sourceMeta)}</span>
        <span>${escapeHtml(fxMeta)}</span>
        <span>${history.length ? `${escapeHtml(history.at(0).date)} -> ${escapeHtml(history.at(-1).date)}` : ""}</span>
      </div>
      ${chartMarkup}
      <div class="metric-row">
        <div class="metric price-dual">
          <span class="muted">Prezzo</span>
          <strong>${formatMoney(signal.quote.price_eur, "EUR")}</strong>
          <small>${formatMoney(signal.quote.price_usd, "USD")}</small>
          <em>Orig. ${escapeHtml(signal.quote.currency)} ${formatPrice(signal.quote.price)}</em>
        </div>
        <div class="metric"><span class="muted">${escapeHtml(rangeLabel(chartRange || activeRange))}</span><strong class="${rangeClass}">${formatPercent(item.range_change_percent)}</strong></div>
        <div class="metric"><span class="muted">Score</span><strong>${signal.score}</strong></div>
      </div>
      ${corporateEventsBlock(item.corporate_events)}
      <div class="reason-line">${signal.reasons.map(escapeHtml).join(" - ")}</div>
      <details class="data-audit">
        <summary>Audit dati</summary>
        <dl>
          ${auditRows.map(([label, value]) => `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`).join("")}
        </dl>
      </details>
      <div class="ticker-news">
        <h3>Notizie ${escapeHtml(ticker.symbol)}</h3>
        ${relatedNews}
      </div>
      <button class="remove" data-symbol="${escapeHtml(ticker.symbol)}" type="button">Rimuovi</button>
    </article>
  `;
}

function corporateEventsBlock(events) {
  if (!events) return "";
  const sourceUrl = events.source_url || "";
  const source = events.source === "alpha_vantage" ? "Alpha Vantage" : "Non disponibile";
  const sourceMarkup = sourceUrl
    ? `<a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">${escapeHtml(source)}</a>`
    : escapeHtml(source);
  const notes = events.notes?.length
    ? `<small>${events.notes.map(escapeHtml).join(" - ")}</small>`
    : "";
  return `
    <div class="corporate-events">
      <div><span>Utili</span><strong>${escapeHtml(formatDate(events.next_earnings_date))}</strong></div>
      <div><span>Dividendo</span><strong>${escapeHtml(formatDate(events.dividend_date))}</strong></div>
      <div><span>Ex-div.</span><strong>${escapeHtml(formatDate(events.ex_dividend_date))}</strong></div>
      <div><span>Fonte</span><strong>${sourceMarkup}</strong></div>
      ${notes}
    </div>
  `;
}

function sourceName(source) {
  if (source === "yahoo") return "Fonte grafico: Yahoo Finance";
  if (source === "alpha_vantage") return "Fonte grafico: Alpha Vantage";
  if (source === "demo") return "Fonte grafico: demo";
  if (source === "unavailable") return "Fonte grafico: non disponibile";
  return `Fonte grafico: ${source || "sconosciuta"}`;
}

function rangeLabel(range) {
  return {
    "1D": "oggi",
    "1W": "ultima settimana",
    "1M": "ultimo mese",
    "1Y": "ultimo anno",
    ALL: "totale",
  }[range] || range;
}

function newsItem(item) {
  const href = item.link && item.link !== "#" ? item.link : "#";
  const openLink = href === "#" ? "" : `<a class="open-news" href="${escapeHtml(href)}" target="_blank" rel="noreferrer">Apri</a>`;
  return `
    <article class="news-item">
      <a href="${escapeHtml(href)}" target="_blank" rel="noreferrer">${escapeHtml(item.title)}</a>
      <p>${escapeHtml(item.summary)}</p>
      <div class="news-meta"><span>${escapeHtml(item.source)}${item.published ? ` - ${escapeHtml(item.published)}` : ""}</span>${openLink}</div>
    </article>
  `;
}

function newsItemCompact(item) {
  const href = item.link && item.link !== "#" ? item.link : "#";
  const disabled = href === "#" ? " news-link-disabled" : "";
  const openLink = href === "#" ? "" : `<a class="open-news" href="${escapeHtml(href)}" target="_blank" rel="noreferrer">Apri</a>`;
  return `
    <article class="ticker-news-item">
      <a class="${disabled}" href="${escapeHtml(href)}" target="_blank" rel="noreferrer">${escapeHtml(item.title)}</a>
      <div class="news-meta"><span>${escapeHtml(item.source)}${item.published ? ` - ${escapeHtml(item.published)}` : ""}</span>${openLink}</div>
    </article>
  `;
}

async function loadSignals() {
  overviewState = await request(`api/overview?range=${encodeURIComponent(activeRange)}&_=${Date.now()}`);
  renderOverview();
}

function renderOverview() {
  const query = filterInput.value.trim().toLowerCase();
  const items = overviewState.filter((item) => {
    const haystack = [
      item.ticker.symbol,
      item.ticker.name,
      item.ticker.sector,
      item.signal.stance,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });

  summaryEl.innerHTML = overviewState.length
    ? [
        summaryTile("Titoli", overviewState.length),
        summaryTile("Bullish", overviewState.filter((item) => item.signal.stance === "Bullish").length),
        summaryTile("Neutrali", overviewState.filter((item) => item.signal.stance === "Neutrale").length),
        summaryTile("Bearish", overviewState.filter((item) => item.signal.stance === "Bearish").length),
      ].join("")
    : "";

  signalsEl.innerHTML = items.length
    ? items.map(insightCard).join("")
    : `<p class="muted">Aggiungi un ticker alla watchlist.</p>`;
  drawCharts();
}

function summaryTile(label, value) {
  return `<div class="summary-tile"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
}

async function loadNews(query = "") {
  const suffix = query ? `?q=${encodeURIComponent(query)}` : "";
  const news = await request(`api/news${suffix}`);
  newsEl.innerHTML = news.length
    ? news.map(newsItem).join("")
    : `<p class="muted">Nessuna notizia trovata.</p>`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const selected = symbolResults.find((item) => item.symbol.toUpperCase() === String(data.get("symbol")).toUpperCase());
  await request("api/tickers", {
    method: "POST",
    body: JSON.stringify({
      symbol: data.get("symbol"),
      name: data.get("name") || selected?.name || null,
      sector: data.get("sector") || selected?.sector || selected?.quote_type || null,
    }),
  });
  form.reset();
  hideSuggestions();
  await loadSignals();
});

signalsEl.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-symbol]");
  if (!button) return;
  await request(`api/tickers/${encodeURIComponent(button.dataset.symbol)}`, { method: "DELETE" });
  await loadSignals();
});

refreshButton.addEventListener("click", async () => {
  await Promise.all([loadSignals(), loadNews(queryInput.value)]);
});

searchButton.addEventListener("click", async () => {
  await loadNews(queryInput.value);
});

filterInput.addEventListener("input", renderOverview);
rangeTabs.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-range]");
  if (!button) return;
  activeRange = button.dataset.range;
  rangeTabs.querySelectorAll("[data-range]").forEach((item) => item.classList.toggle("active", item === button));
  await loadSignals();
});
currencyTabs.addEventListener("click", (event) => {
  const button = event.target.closest("[data-currency]");
  if (!button) return;
  activeCurrency = button.dataset.currency;
  currencyTabs.querySelectorAll("[data-currency]").forEach((item) => item.classList.toggle("active", item === button));
  drawCharts();
});
symbolInput.addEventListener("input", () => {
  clearTimeout(suggestTimer);
  suggestTimer = setTimeout(loadSymbolSuggestions, 220);
});
symbolInput.addEventListener("change", applySelectedSymbol);
document.addEventListener("click", (event) => {
  if (!event.target.closest(".symbol-field")) hideSuggestions();
});
suggestionsEl.addEventListener("click", (event) => {
  const option = event.target.closest("[data-symbol]");
  if (!option) return;
  const item = symbolResults.find((result) => result.symbol === option.dataset.symbol);
  if (!item) return;
  symbolInput.value = item.symbol;
  nameInput.value = item.name || "";
  sectorInput.value = item.sector || item.quote_type || "";
  hideSuggestions();
});

async function loadSymbolSuggestions() {
  const query = symbolInput.value.trim();
  if (query.length < 2) {
    symbolResults = [];
    symbolOptions.innerHTML = "";
    hideSuggestions();
    return;
  }

  try {
    symbolResults = await request(`api/search?q=${encodeURIComponent(query)}&limit=8`);
    symbolOptions.innerHTML = symbolResults
      .map((item) => `<option value="${escapeHtml(item.symbol)}">${escapeHtml(item.name || item.exchange || "")}</option>`)
      .join("");
    suggestionsEl.innerHTML = symbolResults.length
      ? symbolResults.map(symbolSuggestion).join("")
      : `<div class="suggestion-empty">Nessun titolo trovato</div>`;
    suggestionsEl.hidden = false;
  } catch {
    symbolResults = [];
    suggestionsEl.innerHTML = `<div class="suggestion-empty">Ricerca titoli non disponibile</div>`;
    suggestionsEl.hidden = false;
  }
}

function symbolSuggestion(item) {
  const meta = [item.name, item.exchange, item.quote_type].filter(Boolean).join(" - ");
  return `
    <button class="suggestion" type="button" data-symbol="${escapeHtml(item.symbol)}">
      <strong>${escapeHtml(item.symbol)}</strong>
      <span>${escapeHtml(meta)}</span>
    </button>
  `;
}

function applySelectedSymbol() {
  const selected = symbolResults.find((item) => item.symbol.toUpperCase() === symbolInput.value.trim().toUpperCase());
  if (!selected) return;
  nameInput.value = nameInput.value || selected.name || "";
  sectorInput.value = sectorInput.value || selected.sector || selected.quote_type || "";
}

function hideSuggestions() {
  suggestionsEl.hidden = true;
}

function drawCharts() {
  document.querySelectorAll(".chart").forEach((canvas) => {
    if (!canvas.dataset.history) return;
    const points = JSON.parse(canvas.dataset.history || "[]");
    const ctx = canvas.getContext("2d");
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth * ratio;
    const height = canvas.clientHeight * ratio;
    canvas.width = width;
    canvas.height = height;
    ctx.clearRect(0, 0, width, height);
    if (points.length < 2) return;

    const valueKey = activeCurrency === "USD" ? "close_usd" : "close_eur";
    const values = points.map((point) => point[valueKey] ?? point.close);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || 1;
    const padLeft = 74 * ratio;
    const padRight = 14 * ratio;
    const padTop = 16 * ratio;
    const padBottom = 28 * ratio;
    const pad = padLeft;
    const plotWidth = width - padLeft - padRight;
    const plotHeight = height - padTop - padBottom;
    const rising = values.at(-1) >= values[0];
    const lineColor = rising ? "#57d69a" : "#ff7878";

    ctx.strokeStyle = "rgba(154, 168, 181, 0.22)";
    ctx.lineWidth = 1 * ratio;
    ctx.fillStyle = "rgba(237, 242, 247, 0.72)";
    ctx.font = `${11 * ratio}px Inter, system-ui, sans-serif`;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (let i = 0; i < 4; i += 1) {
      const y = padTop + (plotHeight / 3) * i;
      const value = max - (span / 3) * i;
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(width - padRight, y);
      ctx.stroke();
      ctx.fillText(formatMoney(value, activeCurrency), padLeft - 8 * ratio, y);
    }

    const gradient = ctx.createLinearGradient(0, padTop, 0, height - padBottom);
    gradient.addColorStop(0, rising ? "rgba(87, 214, 154, 0.28)" : "rgba(255, 120, 120, 0.24)");
    gradient.addColorStop(1, "rgba(16, 20, 24, 0)");

    ctx.beginPath();
    points.forEach((point, index) => {
      const x = padLeft + (plotWidth * index) / (points.length - 1);
      const closeValue = point[valueKey] ?? point.close;
      const y = padTop + plotHeight - ((closeValue - min) / span) * plotHeight;
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.lineTo(width - padRight, height - padBottom);
    ctx.lineTo(padLeft, height - padBottom);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    ctx.beginPath();
    points.forEach((point, index) => {
      const x = padLeft + (plotWidth * index) / (points.length - 1);
      const closeValue = point[valueKey] ?? point.close;
      const y = padTop + plotHeight - ((closeValue - min) / span) * plotHeight;
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 2.5 * ratio;
    ctx.stroke();

    ctx.fillStyle = "rgba(154, 168, 181, 0.88)";
    ctx.textAlign = "left";
    ctx.textBaseline = "alphabetic";
    ctx.fillText(shortDate(points[0].date), padLeft, height - 8 * ratio);
    ctx.textAlign = "right";
    ctx.fillText(shortDate(points.at(-1).date), width - padRight, height - 8 * ratio);
  });
}

function shortDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("it-IT", {
    day: "2-digit",
    month: "2-digit",
    ...(activeRange === "1D" ? { hour: "2-digit", minute: "2-digit" } : {}),
  }).format(date);
}

window.addEventListener("resize", drawCharts);
Promise.all([loadSignals(), loadNews()]);
