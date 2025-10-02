#!/usr/bin/env bash
export NODE_BROADCAST_URL="http://localhost:4000/broadcast"
# optionally set API_TOKEN="mytoken"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
