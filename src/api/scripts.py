    
import math
from typing import Tuple

def parse_latlon_decimal(value: str) -> Tuple[float, float]:
    try:
        lat_s, lon_s = [p.strip() for p in value.split(",")]
        return float(lat_s), float(lon_s)
    except Exception as e:
        raise ValueError(f"Invalid lat/lon format: {value}") from e


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Возвращает расстояние в метрах между двумя точками (Haversine)."""
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c