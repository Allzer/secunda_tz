import math
from typing import Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from src.models.models import * #ActivitiesModels, BuildingsModel, OrganizationsModels


router = APIRouter(
    prefix="/v1/secunda",
    tags=["clients"]
)

@router.post('/org_in_builds')
def get_builds(org_address: str, session: Session = Depends(get_db)): #builds_name, 
    '''список всех организаций находящихся в конкретном здании'''
    try:
        result_list = []

        query = (
            select(BuildingsModel, OrganizationsModels)
            .join(OrganizationsModels, OrganizationsModels.buildings_id == BuildingsModel.id)
            .where(BuildingsModel.address == org_address)
        )       
        res = session.execute(query)
        
        for building, org in res:
            result = {
                'address': building.address,
                'latitude_longitude': building.latitude_longitude,

                'org_name': org.name
            }
            result_list.append(result)
        return result_list
    except Exception as er:
        print(er)
        raise HTTPException(status_code=500, detail='Не удалось выполнить чтение из БД')

@router.post('/org_by_activiys')
def get_builds(org_activitys: str, session: Session = Depends(get_db)):
    '''список всех организаций, которые относятся к указанному виду деятельности'''
    try:
        result_list = []

        query = (
            select(OrganizationsModels)
            .select_from(OrganizationActivitiesModels)
            .join(ActivitiesModels, OrganizationActivitiesModels.activity_id == ActivitiesModels.id)
            .join(OrganizationsModels, OrganizationActivitiesModels.organization_id == OrganizationsModels.id)
            .where(ActivitiesModels.name == org_activitys)
            .distinct()
        )

        res = session.execute(query).scalars().all()
        for org in res:
            result = {
                'org_id': str(org.id),
                'org_name': org.name
            }
            result_list.append(result)
            
        return result_list
    except Exception as er:
        print(er)
        raise HTTPException(status_code=500, detail='Не удалось выполнить чтение из БД')

def parse_latlon_decimal(value: str) -> Tuple[float, float]:
    try:
        lat_s, lon_s = [p.strip() for p in value.split(",")]
        return float(lat_s), float(lon_s)
    except Exception as e:
        raise ValueError(f"Invalid lat/lon format: {value}") from e

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Возвращает расстояние в метрах между двумя точками (Haversine)."""
    R = 6371000.0  # радиус Земли в метрах
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@router.get('/geo_search_buildings')
def search_buildings_by_geo(
    lat: Optional[float] = Query(None, description="Центр: широта (decimal) — нужен если указан radius_m"),
    lon: Optional[float] = Query(None, description="Центр: долгота (decimal) — нужен если указан radius_m"),
    radius_m: Optional[float] = Query(None, description="Радиус в метрах"),
    min_lat: Optional[float] = Query(None, description="bbox min latitude"),
    max_lat: Optional[float] = Query(None, description="bbox max latitude"),
    min_lon: Optional[float] = Query(None, description="bbox min longitude"),
    max_lon: Optional[float] = Query(None, description="bbox max longitude"),
    session: Session = Depends(get_db)
) -> List[Dict]:
    """
    Поиск зданий (и организаций в них) по radius (с lat/lon) или по bbox (min/max lat/lon).
    Требования:
      - Для radius: укажите lat, lon и radius_m (метры).
      - Для bbox: укажите все min_lat, max_lat, min_lon, max_lon.
      - Можно комбинировать (bbox — предварительная фильтрация).
    """
    try:
        if radius_m is not None:
            if lat is None or lon is None:
                raise HTTPException(status_code=400, detail="Для radius_m необходимо передать lat и lon.")
        use_bbox = (min_lat is not None and max_lat is not None and min_lon is not None and max_lon is not None)
        if not use_bbox and radius_m is None:
            raise HTTPException(status_code=400, detail="Укажите либо radius_m (с lat/lon), либо полный bbox.")

        stmt = select(BuildingsModel)
        buildings = session.execute(stmt).scalars().all()

        results: List[Dict] = []
        for b in buildings:
            try:
                b_lat, b_lon = parse_latlon_decimal(b.latitude_longitude)
            except Exception:
                continue

            if use_bbox:
                if not (min_lat <= b_lat <= max_lat and min_lon <= b_lon <= max_lon):
                    continue

            dist_m = None
            if radius_m is not None:
                dist_m = haversine_m(lat, lon, b_lat, b_lon)
                if dist_m > radius_m:
                    continue

            orgs_stmt = select(OrganizationsModels).where(OrganizationsModels.buildings_id == b.id)
            orgs = session.execute(orgs_stmt).scalars().all()
            orgs_list = [{"org_id": str(o.id), "org_name": o.name} for o in orgs]

            item = {
                "building_id": str(b.id),
                "address": b.address,
                "latitude": b_lat,
                "longitude": b_lon,
                "organizations": orgs_list
            }
            if dist_m is not None:
                item["distance_m"] = round(dist_m, 2)
            results.append(item)

        if radius_m is not None:
            results.sort(key=lambda x: x.get("distance_m", 0.0))

        return results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка поиска: {e}")