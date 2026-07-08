# CivicFlow India: Nationwide Crowdsourced Traffic Coordinator

### 🔗 Live Project Demo
> [!IMPORTANT]
> **Access the Live Web Application here:** ["https://civic-flow-gbv4.onrender.com"]
> 
---

CivicFlow India is a dynamic, nationwide traffic coordination and gridlock resolution platform. It empowers citizens to report active traffic jams, upload real-time visual gridlock photos, and coordinates voluntary traffic responders dynamically on a high-fidelity mapping interface.

---

## 🚀 Key Features

*   **Nationwide OSRM Routing Engine:** Dynamic routing across the entire road network of India. Automatically detects if a path intersects any reported gridlock and issues real-time warnings.
*   **Satellite Hybrid Layer:** Toggleable high-resolution satellite view overlaid with street names, boundaries, and highway details.
*   **Geolocated Landmark Reference Photos:** Automatically fetches geolocated landmark photos using Wikipedia's Geosearch engine when clicking coordinates.
*   **Crowdsourced Traffic Snapshots:** Enables drivers to upload base64 images of gridlocks directly from their devices to show real-time bottlenecks.
*   **Spatial Volunteer Clustering:** Dynamically groups active traffic coordinators within a 100-meter proximity radius using WebSockets for room sync.
*   **Database Persistence & Auto-Expiry:** Persists data using an SQLite database with a 30-minute Time-To-Live (TTL) auto-expiry for traffic reports.

---

## 🛠️ Local Installation & Launch

1.  **Clone the repository** and navigate to the project directory.
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the FastAPI server:**
    ```bash
    python -m uvicorn civicflow.server:app --reload --host 127.0.0.1 --port 8000
    ```
4.  **Open the interface:**
    Navigate to `http://localhost:8000` in your web browser.

---

## 🧪 Running Automated Tests

To execute the integration test suite validating REST APIs, OSRM warning overlays, and SQLite queries:
```bash
python -m pytest civicflow/test_server.py
```
