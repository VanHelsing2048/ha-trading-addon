from app.models import NewsItem, Quote, Signal


POSITIVE_WORDS = {"positivo", "crescita", "ordini", "rialzo", "strong", "beat", "upgrade", "ai"}
NEGATIVE_WORDS = {"negativo", "rischio", "calo", "taglio", "volatile", "weak", "miss", "downgrade"}


def build_signal(symbol: str, quote: Quote, news: list[NewsItem]) -> Signal:
    score = 50
    reasons: list[str] = []

    if quote.change_percent >= 2:
        score += 15
        reasons.append("Momentum giornaliero positivo")
    elif quote.change_percent <= -2:
        score -= 15
        reasons.append("Momentum giornaliero negativo")
    else:
        reasons.append("Prezzo in movimento moderato")

    news_text = " ".join(f"{item.title} {item.summary or ''}" for item in news).lower()
    positive_hits = sum(1 for word in POSITIVE_WORDS if word in news_text)
    negative_hits = sum(1 for word in NEGATIVE_WORDS if word in news_text)

    if positive_hits:
        score += min(20, positive_hits * 5)
        reasons.append("Notizie con parole chiave positive")
    if negative_hits:
        score -= min(20, negative_hits * 5)
        reasons.append("Notizie con parole chiave di rischio")

    score = max(0, min(100, score))
    if score >= 65:
        stance = "Bullish"
    elif score <= 40:
        stance = "Bearish"
    else:
        stance = "Neutrale"

    return Signal(symbol=symbol.upper(), stance=stance, score=score, reasons=reasons, quote=quote, news=news[:5])

