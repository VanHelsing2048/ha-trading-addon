import os
from datetime import datetime, timezone

import feedparser

from app.models import NewsItem


DEFAULT_DEMO_NEWS = [
    {
        "title": "Mercati cauti in attesa dei prossimi dati macro",
        "summary": "Gli investitori restano selettivi sui settori piu esposti ai tassi.",
        "source": "demo",
    },
    {
        "title": "Tecnologia in focus dopo nuovi ordini nel comparto AI",
        "summary": "Il sentiment rimane positivo, ma le valutazioni sono sotto osservazione.",
        "source": "demo",
    },
    {
        "title": "Energia volatile tra scorte e tensioni geopolitiche",
        "summary": "Il settore mostra movimenti rapidi e rischio elevato.",
        "source": "demo",
    },
]


async def get_news(symbols: list[str], query: str | None = None) -> list[NewsItem]:
    urls = [url.strip() for url in os.environ.get("NEWS_RSS_URLS", "").split(",") if url.strip()]
    items: list[NewsItem] = []

    for url in urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:50]:
            title = getattr(entry, "title", "")
            summary = getattr(entry, "summary", "")
            text = f"{title} {summary}".lower()
            matched = [symbol for symbol in symbols if symbol.lower() in text]
            if query and query.lower() not in text:
                continue
            if symbols and not matched and not query:
                continue
            items.append(
                NewsItem(
                    title=title,
                    link=getattr(entry, "link", ""),
                    source=getattr(feed.feed, "title", "rss"),
                    published=getattr(entry, "published", None),
                    summary=summary,
                    symbols=matched,
                )
            )

    if items:
        return items[:100]

    demo_items = []
    now = datetime.now(timezone.utc).isoformat()
    for raw in DEFAULT_DEMO_NEWS:
        title = raw["title"]
        summary = raw["summary"]
        if query and query.lower() not in f"{title} {summary}".lower():
            continue
        demo_items.append(
            NewsItem(
                title=title,
                link="#",
                source=raw["source"],
                published=now,
                summary=summary,
                symbols=symbols[:3],
            )
        )
    return demo_items

