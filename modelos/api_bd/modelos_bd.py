from pydantic import BaseModel
from typing import List, Optional


class Laureate(BaseModel):
    id: Optional[int] = None
    firstname: Optional[str] = None
    surname: Optional[str] = None
    motivation: Optional[str] = None
    share: Optional[str] = None


class Prize(BaseModel):
    year: int
    category: str
    laureates: List[Laureate] = []
    overallMotivation: Optional[str] = None


class PrizesResponse(BaseModel):
    prizes: List[Prize] = []


class LaureateUpdate(BaseModel):
    id: Optional[int] = None
    firstname: Optional[str] = None
    surname: Optional[str] = None
    motivation: Optional[str] = None
    share: Optional[str] = None


class PrizeUpdate(BaseModel):
    laureates: Optional[List[LaureateUpdate]] = None
    overallMotivation: Optional[str] = None