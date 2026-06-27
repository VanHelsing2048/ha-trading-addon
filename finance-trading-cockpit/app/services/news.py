import os

import feedparser

from app.models import NewsItem


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

    return []
