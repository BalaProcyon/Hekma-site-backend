from fastapi import APIRouter
from app.api.endpoints import users
from app.api.endpoints import news_feed

api_router = APIRouter()

# api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(news_feed.router, prefix="/news_feed", tags=["news_feed"])
