from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class StatusResponse(BaseModel):
    code: int
    message: str

class GenericResponse(BaseModel, Generic[T]):
    data: T
    status: StatusResponse
