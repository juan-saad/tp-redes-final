from pydantic import BaseModel
from typing import List, Optional


class Laureate(BaseModel):
    id: int
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
