from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

class NewFeed(BaseModel):
    title: str
    link: str
    published: str
