from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List


class NewFeed(BaseModel):
    title: str
    link: str
    published: str


class NewsItem(BaseModel):
    """Common return type for each item in news list / aggregated responses."""
    id: str
    source: str                         # WHO | NIH | FDA | PubMed | Google
    type: str                           # official | research | news
    title: str
    link: str
    published: str
    recalling_firm: Optional[str] = None  # FDA only


class NewsAggregatedResponse(BaseModel):
    """Return type for the aggregated health-news endpoint."""
    count: int
    data: List[NewsItem]


class NewsItemDetail(BaseModel):
    """Common return type for all individual news-by-id endpoints (WHO, NIH, FDA)."""
    id: str
    source: str                          # WHO | NIH | FDA
    type: str                            # official | research | news
    title: str
    link: str
    published: str
    summary: Optional[str] = None        # WHO / NIH article summary
    # FDA-specific fields (None for RSS sources)
    recalling_firm: Optional[str] = None
    product_description: Optional[str] = None
    product_quantity: Optional[str] = None
    status: Optional[str] = None
    classification: Optional[str] = None
    distribution_pattern: Optional[str] = None


class ImportedArticle(BaseModel):
    title: str
    summary: str
    url: str
    date: str
    externalId: str
    imageUrl: Optional[str] = None
    source: str
    sourceType: str
    category: str
    region: List[str]
    image_emoji: str


class NewsFeedV2Response(BaseModel):
    articles: List[ImportedArticle]


class WHOItemV2(BaseModel):
    title: str
    date: str
    url: str
    type: str


class WHONewsV2Response(BaseModel):
    items: List[WHOItemV2]
