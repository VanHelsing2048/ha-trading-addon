const signalsEl = document.querySelector("#signals");
const newsEl = document.querySelector("#news");
const form = document.querySelector("#ticker-form");
const refreshButton = document.querySelector("#refresh");
const searchButton = document.querySelector("#search-news");
const queryInput = document.querySelector("#news-query");
const filterInput = document.querySelector("#watchlist-filter");
const rangeSelect = document.querySelector("#history-range");
const summaryEl = document.querySelector("#summary");

let overviewState = [];

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

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function signalCard(signal) {
  const changeClass = signal.quote.change_percent >= 0 ? "Bullish" : "Bearish";
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
        <div class="metric"><span class="muted">Oggi</span><strong class="${changeClass}">${signal.quote.change_percent}%</strong></div>
        <div class="metric"><span class="muted">Score</span><strong>${signal.score}</strong></div>
      </div>
      <div class="metric"><span class="muted">Volume</span><strong>${formatVolume(signal.quote.volume)}</strong></div>
      <ul class="reasons">${signal.reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul>
      <button class="remove" data-symbol="${safeSymbol}" type="button">Rimuovi</button>
    </article>
  `;
}

function insightCard(item) {
  const { ticker, signal, history } = item;
  const changeClass = signal.quote.change_percent >= 0 ? "Bullish" : "Bearish";
  const subtitle = [ticker.name, ticker.sector].filter(Boolean).map(escapeHtml).join(" - ");
  const historyJson = escapeHtml(JSON.stringify(history));
  return `
    <article class="signal insight-card">
      <header>
        <div>
          <div class="symbol">${escapeHtml(ticker.symbol)}</div>
          <div class="muted">${subtitle || "Titolo monitorato"}</div>
        </div>
        <span class="stance ${escapeHtml(signal.stance)}">${escapeHtml(signal.stance)}</span>
      </header>
      <canvas class="chart" width="640" height="220" data-history="${historyJson}" aria-label="Andamento ${escapeHtml(ticker.symbol)}"></canvas>
      <div class="metric-row">
        <div class="metric"><span class="muted">Prezzo</span><strong>${formatPrice(signal.quote.price)}</strong></div>
        <div class="metric"><span class="muted">Oggi</span><strong class="${changeClass}">${signal.quote.change_percent}%</strong></div>
        <div class="metric"><span class="muted">Score</span><strong>${signal.score}</strong></div>
      </div>
      <div class="reason-line">${signal.reasons.map(escapeHtml).join(" · ")}</div>
      <button class="remove" data-symbol="${escapeHtml(ticker.symbol)}" type="button">Rimuovi</button>
    </article>
  `;
}

function newsItem(item) {
  const href = item.link && item.link !== "#" ? item.link : "#";
  return `
    <article class="news-item">
      <a href="${escapeHtml(href)}" target="_blank" rel="noreferrer">${escapeHtml(item.title)}</a>
      <p>${escapeHtml(item.summary)}</p>
      <div class="muted">${escapeHtml(item.source)}${item.published ? ` - ${escapeHtml(item.published)}` : ""}</div>
    </article>
  `;
}

async function loadSignals() {
  const days = rangeSelect.value;
  overviewState = await request(`api/overview?days=${encodeURIComponent(days)}`);
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
  await request("api/tickers", {
    method: "POST",
    body: JSON.stringify({
      symbol: data.get("symbol"),
      name: data.get("name") || null,
      sector: data.get("sector") || null,
    }),
  });
  form.reset();
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
rangeSelect.addEventListener("change", loadSignals);

function drawCharts() {
  document.querySelectorAll(".chart").forEach((canvas) => {
    const points = JSON.parse(canvas.dataset.history || "[]");
    const ctx = canvas.getContext("2d");
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth * ratio;
    const height = canvas.clientHeight * ratio;
    canvas.width = width;
    canvas.height = height;
    ctx.clearRect(0, 0, width, height);
    if (points.length < 2) return;

    const values = points.map((point) => point.close);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || 1;
    const pad = 18 * ratio;
    const plotWidth = width - pad * 2;
    const plotHeight = height - pad * 2;
    const rising = values.at(-1) >= values[0];
    const lineColor = rising ? "#57d69a" : "#ff7878";

    ctx.strokeStyle = "rgba(154, 168, 181, 0.22)";
    ctx.lineWidth = 1 * ratio;
    for (let i = 0; i < 4; i += 1) {
      const y = pad + (plotHeight / 3) * i;
      ctx.beginPath();
      ctx.moveTo(pad, y);
      ctx.lineTo(width - pad, y);
      ctx.stroke();
    }

    const gradient = ctx.createLinearGradient(0, pad, 0, height - pad);
    gradient.addColorStop(0, rising ? "rgba(87, 214, 154, 0.28)" : "rgba(255, 120, 120, 0.24)");
    gradient.addColorStop(1, "rgba(16, 20, 24, 0)");

    ctx.beginPath();
    points.forEach((point, index) => {
      const x = pad + (plotWidth * index) / (points.length - 1);
      const y = pad + plotHeight - ((point.close - min) / span) * plotHeight;
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.lineTo(width - pad, height - pad);
    ctx.lineTo(pad, height - pad);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    ctx.beginPath();
    points.forEach((point, index) => {
      const x = pad + (plotWidth * index) / (points.length - 1);
      const y = pad + plotHeight - ((point.close - min) / span) * plotHeight;
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 2.5 * ratio;
    ctx.stroke();
  });
}

window.addEventListener("resize", drawCharts);
Promise.all([loadSignals(), loadNews()]);
