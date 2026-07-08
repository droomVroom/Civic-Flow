# CivicFlow - Crowdsourced Intersection Coordinator

CivicFlow is an advanced crowdsourced traffic coordination and gridlock resolution system designed for unmanaged local intersections.

## Features
- **Dijkstra-based Graph Routing Engine:** Dynamically detours traffic around reported bottlenecks.
- **Geospatial Proximity Alerts:** Notifies users within 1-2 km of active gridlocks.
- **WebSocket Volunteer Coordinator:** Syncs volunteer responders live on a Leaflet map.
- **Interactive Visual Simulator:** Centered on coordinates in Kanpur, India.

## Setup & Running

1. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Start the FastAPI server:**
   ```bash
   python -m uvicorn civicflow.server:app --reload --host 127.0.0.1 --port 8000
   ```
3. **Open the browser:**
   Go to `http://localhost:8000` to view the interactive map.
