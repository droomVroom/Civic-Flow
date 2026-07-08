import os

import json

import uuid

import urllib.request

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException

from fastapi.responses import HTMLResponse, FileResponse

from pydantic import BaseModel

from typing import List, Optional

from civicflow.state import SystemState, calculate_distance

app = FastAPI(title="CivicFlow India - Nationwide Dynamic Traffic Coordinator")

state = SystemState()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

class JamReport(BaseModel):

    lat: float

    lon: float

    status: str  

    image_b64: Optional[str] = None

class RouteRequest(BaseModel):

    start_lat: float

    start_lon: float

    end_lat: float

    end_lon: float

def fetch_osrm_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> dict:

    url = (

        "http://router.project-osrm.org/route/v1/driving/"

        f"{start_lon},{start_lat};{end_lon},{end_lat}"

        "?overview=full&geometries=geojson"

    )

    try:

        req = urllib.request.Request(

            url, 

            headers={"User-Agent": "CivicFlow-India-Academic-Project/1.0"}

        )

        with urllib.request.urlopen(req, timeout=5) as response:

            res_data = json.loads(response.read().decode("utf-8"))

            routes = res_data.get("routes", [])

            if not routes:

                return {"path_found": False, "distance_km": 0.0, "coordinates": []}

            route = routes[0]

            distance_m = route.get("distance", 0.0)

            geometry = route.get("geometry", {})

            raw_coords = geometry.get("coordinates", []) 

            leaflet_coords = [[lat, lon] for lon, lat in raw_coords]

            return {

                "path_found": True,

                "distance_km": round(distance_m / 1000.0, 2),

                "coordinates": leaflet_coords

            }

    except Exception as e:

        print(f"Error fetching path from OSRM: {e}")

        return {"path_found": False, "distance_km": 0.0, "coordinates": [], "error": str(e)}

class WebSocketCoordinator:

    def __init__(self):

        self.connections = {}

    async def register(self, volunteer_id: str, websocket: WebSocket):

        await websocket.accept()

        self.connections[volunteer_id] = websocket

    def unregister(self, volunteer_id: str):

        if volunteer_id in self.connections:

            del self.connections[volunteer_id]

    async def broadcast_to_session(self, session_id: str):

        volunteers_list = state.get_session_volunteers(session_id)

        message = {

            "type": "volunteer_sync",

            "session_id": session_id,

            "volunteers": volunteers_list

        }

        for v in volunteers_list:

            vid = v["id"]

            if vid in self.connections:

                try:

                    await self.connections[vid].send_json(message)

                except Exception:

                    pass

ws_coordinator = WebSocketCoordinator()

@app.get("/", response_class=HTMLResponse)

async def serve_home():

    index_file = os.path.join(TEMPLATES_DIR, "index.html")

    if not os.path.exists(index_file):

        raise HTTPException(status_code=404, detail="Index HTML template not found")

    return FileResponse(index_file)

@app.get("/api/jams")

async def get_jams():

    return state.get_all_jams()

@app.post("/api/report_jam")

async def report_jam(report: JamReport):

    if report.status == "blocked":

        jam_id = state.add_gridlock(report.lat, report.lon, report.image_b64)

        action = f"reported at [{report.lat}, {report.lon}]"

    else:

        state.remove_gridlock(report.lat, report.lon)

        action = f"cleared at [{report.lat}, {report.lon}]"

    return {"status": "success", "message": f"Gridlock {action}.", "jams": state.get_all_jams()}

@app.post("/api/route")

async def get_route(req: RouteRequest):

    result = fetch_osrm_route(req.start_lat, req.start_lon, req.end_lat, req.end_lon)

    if not result.get("path_found", False):

        return {"status": "failed", "message": "No routing path found", "coordinates": []}

    jams = state.get_all_jams()

    warnings = []

    route_coords = result["coordinates"]

    for lat, lon in route_coords:

        for jam in jams:

            dist = calculate_distance(lat, lon, jam["lat"], jam["lon"])

            if dist <= 0.15:

                warnings.append({

                    "id": jam["id"],

                    "lat": jam["lat"],

                    "lon": jam["lon"],

                    "distance_km": round(dist, 3)

                })

                break 

    return {

        "status": "success",

        "distance_km": result["distance_km"],

        "coordinates": route_coords,

        "warnings": warnings

    }

@app.websocket("/ws/rescue")

async def ws_rescue_coordinator(websocket: WebSocket):

    volunteer_id = str(uuid.uuid4())

    await ws_coordinator.register(volunteer_id, websocket)

    current_session_id = None

    try:

        while True:

            data_str = await websocket.receive_text()

            data = json.loads(data_str)

            msg_type = data.get("type")

            name = data.get("name", "Anonymous Volunteer")

            lat = float(data.get("lat", 0.0))

            lon = float(data.get("lon", 0.0))

            if msg_type == "register":

                current_session_id = state.register_volunteer(volunteer_id, name, lat, lon)

                await ws_coordinator.broadcast_to_session(current_session_id)

            elif msg_type == "update":

                old_sid, new_sid = state.update_volunteer_position(volunteer_id, lat, lon)

                if old_sid != new_sid:

                    current_session_id = new_sid

                    await ws_coordinator.broadcast_to_session(old_sid)

                    await ws_coordinator.broadcast_to_session(new_sid)

                else:

                    await ws_coordinator.broadcast_to_session(current_session_id)

    except WebSocketDisconnect:

        ws_coordinator.unregister(volunteer_id)

        old_sid = state.unregister_volunteer(volunteer_id)

        if old_sid:

            await ws_coordinator.broadcast_to_session(old_sid)

    except Exception as e:

        print(f"Error in WebSocket session loop: {e}")

        ws_coordinator.unregister(volunteer_id)

        old_sid = state.unregister_volunteer(volunteer_id)

        if old_sid:

            await ws_coordinator.broadcast_to_session(old_sid)

