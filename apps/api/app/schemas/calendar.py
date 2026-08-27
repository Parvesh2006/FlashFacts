from typing import List, Dict
from pydantic import BaseModel, Field


class CalendarDayStat(BaseModel):
    date: str = Field(..., json_schema_extra={"example": "2026-08-18"})
    total: int = Field(..., json_schema_extra={"example": 25})
    domains: Dict[str, int] = Field(default_factory=dict, json_schema_extra={"example": {"AI": 4, "Politics": 3, "Sports": 7}})


class CalendarResponse(BaseModel):
    month: str = Field(..., json_schema_extra={"example": "2026-08"})
    days: List[CalendarDayStat]
