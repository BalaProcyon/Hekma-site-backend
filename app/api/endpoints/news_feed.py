from fastapi import APIRouter, HTTPException
from app.schemas.news_feed import (
    NewFeed, NewsItemDetail, NewsAggregatedResponse,
    NewsFeedV2Response, WHONewsV2Response
)
from app.schemas.generic import StatusResponse, GenericResponse
from app.services.news_feed_service import (
    get_aggregated_news, get_news_by_id,
    get_news_feed_v2, get_who_news_v2
)
import feedparser
from app.core.config import settings

router = APIRouter()

SUPPORTED_SOURCES = ["WHO", "NIH", "FDA"]


@router.get("/who-news")
def get_who_news():
    try:
        feed = feedparser.parse(settings.WHO_RSS_URL)
        articles = [
            NewFeed(
                title=e.title,
                link=e.link,
                published=e.published
            )
            for e in feed.entries
        ]
        return GenericResponse(data=articles, status=StatusResponse(code=1001, message="Success"))
    except Exception as e:
        return StatusResponse(code=1002, message=str(e))


@router.get("/health-news", response_model=NewsAggregatedResponse)
def get_health_news():
    return get_aggregated_news()


@router.get("/news/{source}/{item_id:path}", response_model=NewsItemDetail)
def get_single_news(source: str, item_id: str):
    """
    Get a single news item by source and id.
    - source: WHO | NIH | FDA
    - item_id: for WHO/NIH this is the article URL (guid); for FDA this is the recall_number
    """
    source_upper = source.strip().upper()
    if source_upper not in SUPPORTED_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported source '{source}'. Supported: {', '.join(SUPPORTED_SOURCES)}"
        )

    result = get_news_by_id(source_upper, item_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No news item found for source='{source_upper}' with id='{item_id}'"
        )

    return result


@router.get("/news-feed/live", response_model=NewsFeedV2Response)
def get_news_feed_live():
    """
    Get the live news feed from WHO, FDA, NIH, and CDC (RSS).
    Matches the frontend /api/news-feed structure.
    """
    return get_news_feed_v2()


@router.get("/who-news/live", response_model=WHONewsV2Response)
def get_who_news_live():
    """
    Get the live WHO news feed from their JSON API.
    Matches the frontend /api/who-news structure.
    """
    return get_who_news_v2()

