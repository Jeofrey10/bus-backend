import time
from typing import Dict
from .models import BusInfo

# In-memory storage for demonstration.
# Swap to DB (Postgres/Mongo) later.
buses: Dict[str, BusInfo] = {}

def upsert_bus(bus_id: str, lat: float, lon: float, speed_kmph: float, heading=None):
    now = time.time()
    buses[bus_id] = BusInfo(
        bus_id=bus_id,
        lat=lat,
        lon=lon,
        speed_kmph=speed_kmph,
        heading=heading,
        last_update=now
    )

def get_bus(bus_id: str):
    return buses.get(bus_id)

def list_buses():
    return list(buses.values())

def remove_stale(threshold_seconds: int = 300):
    """Optional cleanup: remove buses not updated within threshold."""
    cutoff = time.time() - threshold_seconds
    to_del = [k for k,v in buses.items() if v.last_update < cutoff]
    for k in to_del:
        del buses[k]
