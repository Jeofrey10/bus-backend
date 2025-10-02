import math

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Haversine distance in kilometers between two lat/lon points.
    """
    R = 6371.0  # Earth radius km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def compute_eta_minutes(distance_km: float, speed_kmph: float):
    """
    Compute ETA in minutes. If speed is zero or missing return None.
    """
    if speed_kmph and speed_kmph > 0:
        hours = distance_km / speed_kmph
        return hours * 60.0
    return None
