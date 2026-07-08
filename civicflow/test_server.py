from fastapi.testclient import TestClient

from civicflow.server import app, state

client = TestClient(app)

def test_homepage():

    response = client.get("/")

    assert response.status_code == 200

def test_jams_reporting():
    state.conn.execute("DELETE FROM jams")
    state.conn.commit()

    res_report = client.post("/api/report_jam", json={

        "lat": 26.4754,

        "lon": 80.3235,

        "status": "blocked"

    })

    assert res_report.status_code == 200

    res_list = client.get("/api/jams")

    assert res_list.status_code == 200

    jams = res_list.json()

    assert len(jams) == 1

    assert jams[0]["lat"] == 26.4754

    assert jams[0]["lon"] == 80.3235

    res_clear = client.post("/api/report_jam", json={

        "lat": 26.4754,

        "lon": 80.3235,

        "status": "clear"

    })

    assert res_clear.status_code == 200

    res_list2 = client.get("/api/jams")

    assert len(res_list2.json()) == 0

def test_osrm_routing_and_warning():
    state.conn.execute("DELETE FROM jams")
    state.conn.commit()

    client.post("/api/report_jam", json={

        "lat": 26.4755,

        "lon": 80.3236,

        "status": "blocked"

    })

    res_route = client.post("/api/route", json={

        "start_lat": 26.4870,

        "start_lon": 80.2980,

        "end_lat": 26.4754,

        "end_lon": 80.3235

    })

    assert res_route.status_code == 200

    data = res_route.json()

    assert data["status"] == "success"

    assert data["distance_km"] > 0

    assert len(data["coordinates"]) > 0

    assert len(data["warnings"]) > 0

    assert data["warnings"][0]["distance_km"] <= 0.15

