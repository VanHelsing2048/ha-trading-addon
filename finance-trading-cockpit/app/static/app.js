const signalsEl = document.querySelector("#signals");
const newsEl = document.querySelector("#news");
const form = document.querySelector("#ticker-form");
const refreshButton = document.querySelector("#refresh");
const searchButton = document.querySelector("#search-news");
const queryInput = document.querySelector("#news-query");

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
  const signals = await request("api/signals");
  signalsEl.innerHTML = signals.length
    ? signals.map(signalCard).join("")
    : `<p class="muted">Aggiungi un ticker alla watchlist.</p>`;
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

Promise.all([loadSignals(), loadNews()]);
