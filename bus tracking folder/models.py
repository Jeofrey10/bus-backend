from pydantic import BaseModel, Field
from typing import Optional

class BusUpdate(BaseModel):
    bus_id: str = Field(..., example="BUS42")
    lat: float = Field(..., example=20.270)
    lon: float = Field(..., example=85.840)
    speed_kmph: float = Field(..., example=30.0)  # km/h
    heading: Optional[float] = Field(None, example=90.0)  # degrees

class BusInfo(BaseModel):
    bus_id: str
    lat: float
    lon: float
    speed_kmph: float
    heading: Optional[float]
    last_update: float

class ETARequest(BaseModel):
    bus_id: str
    stop_lat: float
    stop_lon: float
