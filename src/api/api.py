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
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@router.get("/geo_search_by_center")
def geo_search_by_center(
    building_id: Optional[str] = Query(None, description="id здания — будет использовано как центр"),
    radius_m: float = Query(..., description="радиус в метрах — обязательный параметр"),
    limit: int = Query(200, description="максимум результатов для защиты от слишком больших ответов"),
    session = Depends(get_db),
    ) -> Dict:
    """Упрощённая ручка: используется один центр (building_id или address) и радиус (radius_m).

    Правила:
      - Передавайте либо building_id, либо address; если переданы оба — приоритет у building_id.
      - radius_m обязателен и задаёт зону поиска вокруг центра.
      - Поиск организаций делается внутри найденных зданий.

    Возвращает: center (id/address/coords), radius_m, count, results (список зданий с организациями и distance_m).
    """
    try:
        # ----- определяем центр -----
        center_lat: Optional[float] = None
        center_lon: Optional[float] = None
        center_id: Optional[str] = None
        center_address: Optional[str] = None

        stmt = select(BuildingsModel).where(BuildingsModel.id == building_id)
        center_b = session.execute(stmt).scalar_one_or_none()
        if center_b is None:
            raise HTTPException(status_code=404, detail="building_id не найден в БД")
        center_id = str(center_b.id)
        center_address = getattr(center_b, "address", None)
        center_lat, center_lon = parse_latlon_decimal(center_b.latitude_longitude)
        

        # ----- собираем здания и фильтруем по radius_m -----
        stmt = select(BuildingsModel)
        buildings = session.execute(stmt).scalars().all()
        results: List[Dict] = []
        for b in buildings:
            try:
                b_lat, b_lon = parse_latlon_decimal(b.latitude_longitude)
            except Exception:
                continue
            dist = haversine_m(center_lat, center_lon, b_lat, b_lon)
            if dist <= radius_m:
                orgs_stmt = select(OrganizationsModels).where(OrganizationsModels.buildings_id == b.id)
                orgs = session.execute(orgs_stmt).scalars().all()
                orgs_list = [{"org_id": str(o.id), "org_name": o.name} for o in orgs]
                results.append({
                    "building_id": str(b.id),
                    "address": getattr(b, "address", None),
                    "latitude": b_lat,
                    "longitude": b_lon,
                    "distance_m": round(dist, 2),
                    "organizations": orgs_list,
                })

            if len(results) >= limit:
                break

        results.sort(key=lambda x: x["distance_m"])

        return {
            "center": {"building_id": center_id, "address": center_address, "latitude": center_lat, "longitude": center_lon},
            "radius_m": radius_m,
            "count": len(results),
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка поиска by_center: {e}")