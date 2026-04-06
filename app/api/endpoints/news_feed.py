# from google.auth import message
from app.schemas.news_feed import NewFeed
from app.schemas.generic import StatusResponse
from app.schemas.generic import GenericResponse
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import feedparser

router = APIRouter()

@router.get("/who-news")
def get_who_news():
    try: 
        feed = feedparser.parse("https://www.who.int/rss-feeds/news-english.xml")
        articles = []
        for entry in feed.entries:
            articles.append(
                NewFeed(
                    title=entry.title,
                    link=entry.link,
                    published=entry.published
                )
            )
        return GenericResponse(data=articles, status=StatusResponse(code=1001, message="Success"))
    except Exception as e:
        return StatusResponse(code=1002, message=str(e))
    
    