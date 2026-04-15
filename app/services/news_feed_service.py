import feedparser
import requests
from datetime import datetime
from app.core.config import settings
from app.schemas.news_feed import (
    NewsItem, NewsItemDetail, NewsAggregatedResponse,
    ImportedArticle, NewsFeedV2Response, WHOItemV2, WHONewsV2Response
)
from typing import Optional, List, Dict, Any
import re
import concurrent.futures


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
        items = [
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
        return sorted(items, key=lambda x: x.published, reverse=True)
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
        items = [
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
        return sorted(items, key=lambda x: x.published, reverse=True)
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
        items = [
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
        return sorted(items, key=lambda x: x.published, reverse=True)
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

    # ISO strings sort correctly as plain strings — no parsing needed
    news = sorted(news, key=lambda x: x.published, reverse=True)

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


# -----------------------------------------------------------------------------
# New News Feed Logic (Replicated from Frontend)
# -----------------------------------------------------------------------------

FEED_CONFIG_V2 = {
    "WHO": {
        "fetchUrl": "https://www.who.int/rss-feeds/news-english.xml",
        "source": "World Health Organization",
        "sourceType": "WHO",
        "category": "Global Health",
        "region": ["Global"],
        "emoji": "🌍",
        "format": "rss",
    },
    "FDA": {
        "fetchUrl": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml",
        "source": "U.S. Food & Drug Administration",
        "sourceType": "FDA",
        "category": "Drug Approval",
        "region": ["US"],
        "emoji": "💊",
        "format": "rss",
    },
    "NIH": {
        "fetchUrl": "https://www.nih.gov/news-releases/feed.xml",
        "source": "National Institutes of Health",
        "sourceType": "NIH",
        "category": "Research Breakthrough",
        "region": ["US"],
        "emoji": "🔬",
        "format": "rss",
    },
    "CDC": {
        "fetchUrl": "https://www.cdc.gov/mmwr/rss/mmwr.xml",
        "source": "Centers for Disease Control",
        "sourceType": "CDC",
        "category": "Public Health",
        "region": ["US"],
        "emoji": "📊",
        "format": "rss",
    },
}


def extract_tag(xml: str, tag: str) -> str:
    pattern = rf"<{tag}[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</{tag}>"
    match = re.search(pattern, xml, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def extract_attr(xml: str, tag: str, attr: str) -> Optional[str]:
    pattern = rf"<{tag}[^>]*\s{attr}=\"([^\"]*)\""
    match = re.search(pattern, xml, re.IGNORECASE)
    return match.group(1) if match else None


def parse_pub_date_v2(raw: str) -> str:
    if not raw:
        return datetime.now().strftime("%Y-%m-%d")

    # NIH format: "Wed, 04/08/2026 - 17:32"  →  MM/DD/YYYY
    nih_match = re.search(r"(\d{2})/(\d{2})/(\d{4})", raw)
    if nih_match:
        mm, dd, yyyy = nih_match.groups()
        return f"{yyyy}-{mm}-{dd}"

    try:
        # Try some common formats
        for fmt in ["%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%SZ"]:
            try:
                dt = datetime.strptime(raw, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
    except:
        pass
    return datetime.now().strftime("%Y-%m-%d")


def parse_rss_items(xml: str, defaults: Dict[str, Any]) -> List[ImportedArticle]:
    chunks = re.split(r"<item[\s>]", xml, flags=re.IGNORECASE)[1:]
    items = []
    for chunk in chunks:
        title = extract_tag(chunk, "title")
        if not title:
            continue
        summary = extract_tag(chunk, "description")
        link = extract_tag(chunk, "link") or extract_attr(chunk, "atom:link", "href") or ""
        guid = extract_tag(chunk, "guid")
        pubDate = extract_tag(chunk, "pubDate") or extract_tag(chunk, "dc:date") or extract_tag(chunk, "pubdate")
        date = parse_pub_date_v2(pubDate)
        mediaUrl = extract_attr(chunk, "media:content", "url") or extract_attr(chunk, "enclosure", "url")
        url = link or guid or ""
        externalId = f"{defaults.get('sourceType')}-{guid or link or title}"[:255]

        items.append(ImportedArticle(
            title=title,
            summary=summary,
            url=url,
            date=date,
            externalId=externalId,
            imageUrl=mediaUrl,
            source=defaults.get("source", ""),
            sourceType=defaults.get("sourceType", ""),
            category=defaults.get("category", "Global Health"),
            region=defaults.get("region", ["Global"]),
            image_emoji=defaults.get("image_emoji", "📰")
        ))
    return items


def fetch_og_image(url: str) -> Optional[str]:
    if not url or not url.startswith("http"):
        return None
    try:
        headers = {
            "User-Agent": "HEKMA-NewsBot/1.0",
            "Accept": "text/html",
        }
        res = requests.get(url, headers=headers, timeout=4, stream=True)
        if res.status_code != 200:
            return None

        # Read only first 8KB
        html = ""
        for chunk in res.iter_content(chunk_size=8192, decode_unicode=True):
            html += chunk
            if len(html) >= 8192:
                break
        
        # Try og:image
        og_match = re.search(r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html, re.I) or \
                   re.search(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', html, re.I)
        
        # Fallback: twitter:image
        tw_match = re.search(r'name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)["\']', html, re.I) or \
                   re.search(r'content=["\']([^"\']+)["\'][^>]*name=["\']twitter:image["\']', html, re.I)
        
        raw_img = og_match.group(1) if og_match else (tw_match.group(1) if tw_match else None)
        if not raw_img:
            return None

        if raw_img.startswith("//"):
            return f"https:{raw_img}"
        if raw_img.startswith("/"):
            from urllib.parse import urljoin
            return urljoin(url, raw_img)
        return raw_img if raw_img.startswith("http") else None
    except:
        return None


def fetch_feed_articles_v2(source_name: str) -> List[ImportedArticle]:
    config = FEED_CONFIG_V2.get(source_name)
    if not config:
        return []
    try:
        headers = {
            "Accept": "application/json" if config["format"] == "json" else "application/xml, text/xml, */*",
            "User-Agent": "HEKMA-NewsBot/1.0",
        }
        res = requests.get(config["fetchUrl"], headers=headers, timeout=10)
        if res.status_code != 200:
            return []

        if config["format"] == "json":
            return []
        else:
            xml = res.text
            return parse_rss_items(xml, {
                "source": config["source"],
                "sourceType": config["sourceType"],
                "category": config["category"],
                "region": config["region"],
                "image_emoji": config["emoji"],
            })
    except:
        return []


def get_news_feed_v2() -> NewsFeedV2Response:
    sources = ["WHO", "FDA", "NIH", "CDC"]
    all_articles = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_source = {executor.submit(fetch_feed_articles_v2, s): s for s in sources}
        for future in concurrent.futures.as_completed(future_to_source):
            try:
                articles = future.result()
                all_articles.extend(articles[:15])  # Cap per source
            except:
                pass

    # Sort newest first
    all_articles.sort(key=lambda x: x.date, reverse=True)

    # Enrich top articles with OG images (up to 20)
    top_limit = 20
    top_articles = all_articles[:top_limit]
    remaining_articles = all_articles[top_limit:]

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for article in top_articles:
            if not article.imageUrl:
                futures.append(executor.submit(lambda a: (a, fetch_og_image(a.url)), article))
            else:
                futures.append(None)
        
        enriched_top = []
        for i, future in enumerate(futures):
            article = top_articles[i]
            if future:
                try:
                    _, img_url = future.result()
                    if img_url:
                        article_dict = article.dict()
                        article_dict['imageUrl'] = img_url
                        enriched_top.append(ImportedArticle(**article_dict))
                    else:
                        enriched_top.append(article)
                except:
                    enriched_top.append(article)
            else:
                enriched_top.append(article)

    return NewsFeedV2Response(articles=enriched_top + remaining_articles)


def get_who_news_v2() -> WHONewsV2Response:
    try:
        url = "https://www.who.int/api/news/newsitems?sf_culture=en&$orderby=PublicationDateAndTime%20desc&$top=12"
        headers = {"Accept": "application/json"}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return WHONewsV2Response(items=[])
        
        data = res.json()
        raw_items = data if isinstance(data, list) else data.get("value", [])
        
        items = []
        for item in raw_items:
            raw_path = item.get("ItemDefaultUrl", "")
            if raw_path:
                if raw_path.startswith("/news"):
                    full_url = f"https://www.who.int{raw_path}"
                else:
                    full_url = f"https://www.who.int/news/item{raw_path}"
            else:
                full_url = "https://www.who.int/news"
            
            items.append(WHOItemV2(
                title=item.get("Title", ""),
                date=item.get("FormatedDate") or item.get("PublicationDateAndTime") or "",
                url=full_url,
                type=item.get("NewsType") or "Update"
            ))
        return WHONewsV2Response(items=items)
    except Exception as e:
        print("WHO news v2 error:", e)
        return WHONewsV2Response(items=[])
