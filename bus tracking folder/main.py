import os
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
import time
import httpx

from .models import BusUpdate, ETARequest
from .storage import upsert_bus, get_bus, list_buses, remove_stale
from .utils import haversine_km, compute_eta_minutes

# Configuration
NODE_REALTIME_BROADCAST_URL = os.getenv("NODE_BROADCAST_URL", "http://localhost:4000/broadcast")
API_TOKEN = os.getenv("API_TOKEN", "")  # optional simple auth token passed in headers

app = FastAPI(title="TransitTracker Backend (FastAPI)")

# Allow CORS from frontend and websocket server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

http_client = httpx.AsyncClient(timeout=5.0)

@app.on_event("startup")
async def startup_event():
    # Could start background tasks here, e.g. stale cleanup
    app.state.cleanup_task = asyncio.create_task(_periodic_cleanup())

@app.on_event("shutdown")
async def shutdown_event():
    app.state.cleanup_task.cancel()
    await http_client.aclose()

async def _periodic_cleanup():
    while True:
        try:
            remove_stale(300)
        except Exception:
            pass
        await asyncio.sleep(60)  # run cleanup every minute

def _auth_valid(token: str) -> bool:
    if not API_TOKEN:
        return True
    return token == API_TOKEN

@app.post("/bus/update")
async def bus_update(payload: BusUpdate, background_tasks: BackgroundTasks, authorization: str = ""):
    """
    Receive GPS and speed updates from buses (or bus gateway).
    Example payload:
    {
      "bus_id":"BUS42",
      "lat": 20.27,
      "lon": 85.84,
      "speed_kmph": 28.5
    }
    """
    # Basic header token checking if API_TOKEN set (simple private auth)
    auth_header = authorization
    if API_TOKEN and not _auth_valid(auth_header):
        raise HTTPException(status_code=403, detail="Invalid API token")

    # store locally
    upsert_bus(payload.bus_id, payload.lat, payload.lon, payload.speed_kmph, getattr(payload, "heading", None))

    # prepare broadcast payload
    broadcast = {
        "type": "bus_update",
        "bus_id": payload.bus_id,
        "lat": payload.lat,
        "lon": payload.lon,
        "speed_kmph": payload.speed_kmph,
        "ts": time.time()
    }

    # send to Node realtime server in background to avoid slowing ingestion
    background_tasks.add_task(_notify_realtime_server, broadcast)

    return {"status": "ok", "bus": payload.bus_id}

async def _notify_realtime_server(payload: Any):
    try:
        # POST JSON to Node realtime server's /broadcast endpoint
        await http_client.post(NODE_REALTIME_BROADCAST_URL, json=payload)
    except Exception:
        # fail silently for now; consider retry/backoff in prod
        pass

@app.get("/bus/list")
def api_list_buses():
    """
    Return all active buses with last-known positions.
    """
    buses = list_buses()
    return {"count": len(buses), "buses": [b.dict() for b in buses]}

@app.post("/eta")
def api_eta(req: ETARequest):
    """
    Calculate ETA (in minutes) for a given bus to a stop coordinate.
    """
    bus = get_bus(req.bus_id)
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    distance = haversine_km(bus.lat, bus.lon, req.stop_lat, req.stop_lon)
    eta_min = compute_eta_minutes(distance, bus.speed_kmph)

    return {
        "bus_id": req.bus_id,
        "distance_km": distance,
        "eta_minutes": eta_min,
        "bus_location": {"lat": bus.lat, "lon": bus.lon, "speed_kmph": bus.speed_kmph}
    }

@app.get("/health")
def health():
    return {"status": "ok"}
