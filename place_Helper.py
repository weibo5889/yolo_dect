import math
import sqlite3


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # 地球半徑 (公里)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def get_nearby_places(lat, lng, max_distance_km=5, db_path='buildings.db'):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT name, address, type, lat, lng FROM places")
    places = cur.fetchall()
    con.close()
    results = []
    for name, address, type_, plat, plng in places:
        if plat is not None and plng is not None:
            distance = haversine(lat, lng, plat, plng)
            if distance <= max_distance_km:
                results.append((name, address, type_, distance))
    results.sort(key=lambda x: x[3])
    return results
