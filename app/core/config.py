import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hekma Backend"
    VERSION: str = "0.1.0"
    DATABASE_URL: str = ""   # Must be set via environment variable on Render
    APP_ENV: str = "dev"
    
    # News Feed URLs
    WHO_RSS_URL: str = "https://www.who.int/rss-feeds/news-english.xml"
    NIH_RSS_URL: str = "https://www.nih.gov/news-events/news-releases/feed"
    FDA_API_URL: str = "https://api.fda.gov/drug/enforcement.json"
    PUBMED_SEARCH_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    PUBMED_SUMMARY_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    GOOGLE_NEWS_RSS_URL: str = "https://news.google.com/rss/search?q=health+site:reuters.com+OR+site:bbc.com+OR+site:theguardian.com"

@lru_cache()
def get_settings() -> Settings:
    app_env = os.getenv("APP_ENV", "dev")
    env_file = f".env.{app_env}"
    if not os.path.exists(env_file):
        env_file = ".env"

    return Settings(
        _env_file=env_file, 
        _env_file_encoding="utf-8"
    )

settings = get_settings()
