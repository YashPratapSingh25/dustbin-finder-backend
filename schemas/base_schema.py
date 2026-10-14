from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

class BaseRequestSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

class BaseResponseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

class ApiResponseSchema(BaseModel, Generic[T]):
    message : str
    result : T

class PaginationMetaData(BaseModel):
    has_next : bool
    has_previous : bool
    page_number : int
    total_pages : int
    page_size : int
    total_items : int

class PaginatedResponseSchema(BaseModel, Generic[T]):
    result : list[T]
    message : str
    metadata : PaginationMetaData

class PaginatedServiceResponse(BaseModel, Generic[T]):
    total_items : int
    result : list[T]

class Pagination(BaseModel):
    limit : int
    offset : int
    page_number : int
    page_size : int