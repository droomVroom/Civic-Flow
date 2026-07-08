import math

import uuid

import sqlite3

import time

import os

DB_FILE = "/data/civicflow.db" if os.path.exists("/data") else "civicflow.db"

def calculate_distance(lat1, lon1, lat2, lon2) -> float:

    R = 6371.0  

    phi1 = math.radians(lat1)

    phi2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)

    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2) ** 2 +

         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

class SystemState:

    def __init__(self):

        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)

        self.create_table()

        self.volunteers = {}

        self.sessions = {}

    def create_table(self):

        cursor = self.conn.cursor()

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS jams ("
            "key_lat_lon TEXT PRIMARY KEY, "
            "id TEXT, "
            "lat REAL, "
            "lon REAL, "
            "image_b64 TEXT, "
            "expires_at REAL"
            ")"
        )

        self.conn.commit()

    def add_gridlock(self, lat: float, lon: float, image_b64: str = None) -> str:

        key = f"{round(lat, 4)},{round(lon, 4)}"

        expires_at = time.time() + 1800.0

        cursor = self.conn.cursor()

        cursor.execute("SELECT id, image_b64 FROM jams WHERE key_lat_lon = ?", (key,))

        row = cursor.fetchone()

        if not row:

            jam_id = str(uuid.uuid4())

            cursor.execute(

                "INSERT INTO jams (key_lat_lon, id, lat, lon, image_b64, expires_at) VALUES (?, ?, ?, ?, ?, ?)",

                (key, jam_id, lat, lon, image_b64, expires_at)

            )

        else:

            jam_id = row[0]

            img = image_b64 if image_b64 else row[1]

            cursor.execute(

                "UPDATE jams SET image_b64 = ?, expires_at = ? WHERE key_lat_lon = ?",

                (img, expires_at, key)

            )

        self.conn.commit()

        return jam_id

    def remove_gridlock(self, lat: float, lon: float):

        key = f"{round(lat, 4)},{round(lon, 4)}"

        cursor = self.conn.cursor()

        cursor.execute("DELETE FROM jams WHERE key_lat_lon = ?", (key,))

        self.conn.commit()

    def get_all_jams(self) -> list:

        now = time.time()

        cursor = self.conn.cursor()

        cursor.execute("DELETE FROM jams WHERE expires_at <= ?", (now,))

        self.conn.commit()

        cursor.execute("SELECT id, lat, lon, image_b64 FROM jams")

        rows = cursor.fetchall()

        return [

            {

                "id": r[0], 

                "lat": r[1], 

                "lon": r[2], 

                "image_b64": r[3]

            }

            for r in rows

        ]

    def get_or_create_session(self, lat: float, lon: float) -> str:

        for sid, sinfo in self.sessions.items():

            dist = calculate_distance(lat, lon, sinfo["center_lat"], sinfo["center_lon"])

            if dist <= 0.1:  

                return sid

        sid = str(uuid.uuid4())

        self.sessions[sid] = {

            "center_lat": lat,

            "center_lon": lon,

            "volunteers": set()

        }

        return sid

    def register_volunteer(self, volunteer_id: str, name: str, lat: float, lon: float) -> str:

        sid = self.get_or_create_session(lat, lon)

        self.volunteers[volunteer_id] = {

            "name": name,

            "lat": lat,

            "lon": lon,

            "session_id": sid

        }

        self.sessions[sid]["volunteers"].add(volunteer_id)

        return sid

    def update_volunteer_position(self, volunteer_id: str, lat: float, lon: float) -> tuple:

        if volunteer_id not in self.volunteers:

            return None, None

        old_sid = self.volunteers[volunteer_id]["session_id"]

        sinfo = self.sessions[old_sid]

        dist = calculate_distance(lat, lon, sinfo["center_lat"], sinfo["center_lon"])

        if dist <= 0.15:

            self.volunteers[volunteer_id]["lat"] = lat

            self.volunteers[volunteer_id]["lon"] = lon

            return old_sid, old_sid

        else:

            sinfo["volunteers"].remove(volunteer_id)

            if not sinfo["volunteers"]:

                del self.sessions[old_sid]

            new_sid = self.get_or_create_session(lat, lon)

            self.volunteers[volunteer_id]["lat"] = lat

            self.volunteers[volunteer_id]["lon"] = lon

            self.volunteers[volunteer_id]["session_id"] = new_sid

            self.sessions[new_sid]["volunteers"].add(volunteer_id)

            return old_sid, new_sid

    def unregister_volunteer(self, volunteer_id: str) -> str:

        if volunteer_id in self.volunteers:

            sid = self.volunteers[volunteer_id]["session_id"]

            if sid in self.sessions:

                self.sessions[sid]["volunteers"].remove(volunteer_id)

                if not self.sessions[sid]["volunteers"]:

                    del self.sessions[sid]

            del self.volunteers[volunteer_id]

            return sid

        return None

    def get_session_volunteers(self, session_id: str) -> list:

        if session_id not in self.sessions:

            return []

        return [

            {

                "id": vid, 

                "name": self.volunteers[vid]["name"], 

                "lat": self.volunteers[vid]["lat"], 

                "lon": self.volunteers[vid]["lon"]

            }

            for vid in self.sessions[session_id]["volunteers"]

        ]

