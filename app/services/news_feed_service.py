import feedparser
import requests
from datetime import datetime
from app.core.config import settings
from app.schemas.news_feed import NewsItem, NewsItemDetail, NewsAggregatedResponse
from typing import Optional, List


def safe_get(value, default=""):
    return value if value else default


# Date formats tried in order when parsing raw source strings
_DATE_FORMATS = [
    "%a, %d %b %Y %H:%M:%S %z",   # RSS with tz:  "Tue, 15 Apr 2026 05:00:00 +0000"
    "%a, %d %b %Y %H:%M:%S",       # RSS no tz:    "Tue, 15 Apr 2026 05:00:00"
    "%Y%m%d",                       # FDA:          "20260415"
    "%Y %b %d",                     # PubMed full:  "2026 Apr 15"
    "%Y %b",                        # PubMed short: "2026 Apr"
    "%Y-%m-%dT%H:%M:%SZ",           # ISO 8601
    "%Y-%m-%d",                     # Simple date
]


def normalize_date(raw: str) -> str:
    """
    Parse a raw date string from any supported source and return a
    standardised UTC ISO 8601 string: 'YYYY-MM-DDTHH:MM:SSZ'.
    Returns empty string if parsing fails.
    """
    if not raw:
        return ""
    raw = raw.strip()
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(raw[:len(fmt) + 5], fmt)  # +5 for tz offset chars
            # If tz-aware, convert to UTC; otherwise assume UTC
            if dt.tzinfo is not None:
                from datetime import timezone
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    return ""


def parse_date(date_str: str) -> datetime:
    """Used internally for sorting. Accepts normalised ISO string or raw string."""
    for fmt in ["%Y-%m-%dT%H:%M:%SZ"] + _DATE_FORMATS:
        try:
            return datetime.strptime(date_str[:25], fmt)
        except (ValueError, TypeError):
            continue
    return datetime.min


# -------------------------------
# WHO (RSS)
# -------------------------------

def fetch_who() -> List[NewsItem]:
    try:
        feed = feedparser.parse(settings.WHO_RSS_URL)
        return [
            NewsItem(
                id=safe_get(e.get("id"), e.get("link", "")),
                source="WHO",
                type="official",
                title=e.get("title", ""),
                link=e.get("link", ""),
                published=normalize_date(safe_get(e.get("published")))
            )
            for e in feed.entries[:5]
        ]
    except Exception as e:
        print("WHO error:", e)
        return []


def get_who_by_id(item_id: str) -> Optional[NewsItemDetail]:
    """Fetch a single WHO news entry by its guid/link id."""
    try:
        feed = feedparser.parse(settings.WHO_RSS_URL)
        for e in feed.entries:
            entry_id = safe_get(e.get("id"), e.get("link", ""))
            if entry_id == item_id:
                return NewsItemDetail(
                    id=entry_id,
                    source="WHO",
                    type="official",
                    title=e.get("title", ""),
                    link=e.get("link", ""),
                    summary=safe_get(e.get("summary")),
                    published=normalize_date(safe_get(e.get("published")))
                )
        return None
    except Exception as e:
        print("WHO by-id error:", e)
        return None

# -------------------------------
# NIH (RSS)
# -------------------------------

def fetch_nih() -> List[NewsItem]:
    try:
        feed = feedparser.parse(settings.NIH_RSS_URL)
        return [
            NewsItem(
                id=safe_get(e.get("id"), e.get("link", "")),
                source="NIH",
                type="official",
                title=e.get("title", ""),
                link=e.get("link", ""),
                published=normalize_date(safe_get(e.get("published")))
            )
            for e in feed.entries[:5]
        ]
    except Exception as e:
        print("NIH error:", e)
        return []


def get_nih_by_id(item_id: str) -> Optional[NewsItemDetail]:
    """Fetch a single NIH news entry by its guid/link id."""
    try:
        feed = feedparser.parse(settings.NIH_RSS_URL)
        for e in feed.entries:
            entry_id = safe_get(e.get("id"), e.get("link", ""))
            if entry_id == item_id:
                return NewsItemDetail(
                    id=entry_id,
                    source="NIH",
                    type="official",
                    title=e.get("title", ""),
                    link=e.get("link", ""),
                    summary=safe_get(e.get("summary")),
                    published=normalize_date(safe_get(e.get("published")))
                )
        return None
    except Exception as e:
        print("NIH by-id error:", e)
        return None


# -------------------------------
# FDA (API)
# -------------------------------

def fetch_fda() -> List[NewsItem]:
    try:
        url = f"{settings.FDA_API_URL}?limit=5"
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            return []
        data = res.json()
        return [
            NewsItem(
                id=item.get("recall_number", ""),
                source="FDA",
                type="official",
                title=item.get("reason_for_recall", "FDA Update"),
                link="",
                published=normalize_date(item.get("report_date", "")),
                recalling_firm=item.get("recalling_firm")
            )
            for item in data.get("results", [])
        ]
    except Exception as e:
        print("FDA error:", e)
        return []


def get_fda_by_id(recall_number: str) -> Optional[NewsItemDetail]:
    """Fetch a single FDA enforcement record by recall_number."""
    try:
        url = f"{settings.FDA_API_URL}?search=recall_number:\"{recall_number}\"&limit=1"
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            return None
        items = res.json().get("results", [])
        if not items:
            return None
        item = items[0]
        return NewsItemDetail(
            id=item.get("recall_number", ""),
            source="FDA",
            type="official",
            title=item.get("reason_for_recall", "FDA Update"),
            link="",
            published=normalize_date(item.get("report_date", "")),
            recalling_firm=item.get("recalling_firm"),
            product_description=item.get("product_description"),
            product_quantity=item.get("product_quantity"),
            status=item.get("status"),
            classification=item.get("classification"),
            distribution_pattern=item.get("distribution_pattern")
        )
    except Exception as e:
        print("FDA by-id error:", e)
        return None


# -------------------------------
# PubMed
# -------------------------------

def fetch_pubmed() -> list:
    try:
        params = {"db": "pubmed", "term": "health", "retmode": "json", "retmax": 5}
        res = requests.get(settings.PUBMED_SEARCH_URL, params=params, timeout=5).json()
        ids = res.get("esearchresult", {}).get("idlist", [])

        if not ids:
            return []

        summary_res = requests.get(settings.PUBMED_SUMMARY_URL, params={
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "json"
        }, timeout=5).json()

        result = []
        for id in ids:
            item = summary_res.get("result", {}).get(id, {})
            result.append({
                "source": "PubMed",
                "type": "research",
                "title": item.get("title", ""),
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{id}/",
                "published": item.get("pubdate", "")
            })
        return result
    except Exception as e:
        print("PubMed error:", e)
        return []


# -------------------------------
# Google News (RSS)
# -------------------------------

def fetch_google() -> list:
    try:
        feed = feedparser.parse(settings.GOOGLE_NEWS_RSS_URL)
        return [{
            "source": "Google",
            "type": "news",
            "title": e.get("title", ""),
            "link": e.get("link", ""),
            "published": safe_get(e.get("published"))
        } for e in feed.entries[:5]]
    except Exception as e:
        print("Google error:", e)
        return []


# -------------------------------
# Aggregator
# -------------------------------

def get_aggregated_news() -> NewsAggregatedResponse:
    who = fetch_who()
    nih = fetch_nih()
    fda = fetch_fda()
    # pubmed = fetch_pubmed()
    # google = fetch_google()

    print("WHO:", len(who))
    print("NIH:", len(nih))
    print("FDA:", len(fda))

    news: List[NewsItem] = []
    news.extend(who)
    news.extend(nih)
    news.extend(fda)
    # news.extend(pubmed)
    # news.extend(google)

    news = sorted(
        news,
        key=lambda x: parse_date(x.published),
        reverse=True
    )

    return NewsAggregatedResponse(count=len(news), data=news)


# -------------------------------
# Get Single News Item (Dispatcher)
# -------------------------------

SOURCE_HANDLERS = {
    "WHO": get_who_by_id,
    "NIH": get_nih_by_id,
    "FDA": get_fda_by_id,
}


def get_news_by_id(source: str, item_id: str) -> Optional[NewsItemDetail]:
    """
    Dispatcher: fetch a single news item by source name and its id.
    Supported sources: WHO, NIH, FDA
    - WHO / NIH: item_id is the entry guid (usually the article URL)
    - FDA: item_id is the recall_number (e.g. 'Z-0001-2024')
    Returns a NewsItemDetail or None if not found.
    """
    source_upper = source.strip().upper()
    handler = SOURCE_HANDLERS.get(source_upper)
    if handler is None:
        return None
    return handler(item_id)
