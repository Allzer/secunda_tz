from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.scripts import bbox_for_radius, haversine_m, parse_latlon_decimal
from database import get_db
from src.models.models import *
from sqlalchemy.orm import aliased

router = APIRouter(
    prefix="/v1/secunda",
    tags=["clients"]
)

@router.get('/org_in_builds')
def get_org_in_builds(org_address: str, session: Session = Depends(get_db)): 
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

@router.get('/org_by_activiys')
def get_org_by_activiys(org_activities: str, session: Session = Depends(get_db)):
    '''список всех организаций, которые относятся к указанному виду деятельности'''
    try:
        result_list = []

        query = (
            select(OrganizationsModels)
            .select_from(OrganizationActivitiesModels)
            .join(ActivitiesModels, OrganizationActivitiesModels.activity_id == ActivitiesModels.id)
            .join(OrganizationsModels, OrganizationActivitiesModels.organization_id == OrganizationsModels.id)
            .where(ActivitiesModels.name == org_activities)
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

@router.get("/geo_search_by_center")
def geo_search_by_center(
    building_id: str = Query(..., description="id здания — будет использовано как центр"),
    radius_m: float = Query(..., description="радиус в метрах — обязательный параметр"),
    limit: int = Query(200, description="максимум результатов для защиты от слишком больших ответов"),
    session: Session = Depends(get_db),
) -> Dict:
    """
    Поиск зданий и организаций в радиусе относительно здания по building_id.
    """
    try:
        center_b = session.execute(select(BuildingsModel).where(BuildingsModel.id == building_id)).scalar_one_or_none()
        if center_b is None:
            raise HTTPException(status_code=404, detail="building_id не найден в БД")

        try:
            center_lat, center_lon = parse_latlon_decimal(center_b.latitude_longitude)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Некорректные координаты у центра")

        min_lat, max_lat, min_lon, max_lon = bbox_for_radius(center_lat, center_lon, radius_m)

        stmt = select(BuildingsModel).where(BuildingsModel.latitude_longitude.isnot(None))
        buildings = session.execute(stmt).scalars().all()

        found = []
        found_building_ids = []

        for b in buildings:
            try:
                b_lat, b_lon = parse_latlon_decimal(b.latitude_longitude)
            except Exception:
                continue

            if not (min_lat <= b_lat <= max_lat and min_lon <= b_lon <= max_lon):
                continue

            dist = haversine_m(center_lat, center_lon, b_lat, b_lon)
            if dist <= radius_m:
                found.append({
                    "building_id": str(b.id),
                    "address": getattr(b, "address", None),
                    "latitude": b_lat,
                    "longitude": b_lon,
                    "distance_m": round(dist, 2),
                })
                found_building_ids.append(b.id)

            if len(found) >= limit:
                break

        if not found:
            return {
                "center": {"building_id": str(center_b.id), "address": getattr(center_b, "address", None),
                           "latitude": center_lat, "longitude": center_lon},
                "radius_m": radius_m,
                "count": 0,
                "results": []
            }

        orgs_stmt = select(OrganizationsModels).where(OrganizationsModels.buildings_id.in_(found_building_ids))
        orgs = session.execute(orgs_stmt).scalars().all()

        orgs_by_building = {}
        for o in orgs:
            orgs_by_building.setdefault(str(o.buildings_id), []).append({"org_id": str(o.id), "org_name": o.name})

        for r in found:
            r["organizations"] = orgs_by_building.get(r["building_id"], [])

        found.sort(key=lambda x: x["distance_m"])
        results = found[:limit]

        return {
            "center": {"building_id": str(center_b.id), "address": getattr(center_b, "address", None),
                       "latitude": center_lat, "longitude": center_lon},
            "radius_m": radius_m,
            "count": len(results),
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка поиска by_center")
    
@router.get('/organization/{organization_id}')
def get_organization_by_id(organization_id: str, session: Session = Depends(get_db)):
    '''получение информации об организации по её идентификатору'''
    try:
        query = (
            select(OrganizationsModels, BuildingsModel)
            .join(BuildingsModel, OrganizationsModels.buildings_id == BuildingsModel.id)
            .where(OrganizationsModels.id == organization_id)
        )
        result = session.execute(query).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Организация не найдена")
        
        org, building = result

        phones_query = select(OrganizationPhonesModels.phone_number).where(
            OrganizationPhonesModels.organization_id == organization_id
        )
        phones = session.execute(phones_query).scalars().all()

        activities_query = (
            select(ActivitiesModels.name)
            .select_from(OrganizationActivitiesModels)
            .join(ActivitiesModels, OrganizationActivitiesModels.activity_id == ActivitiesModels.id)
            .where(OrganizationActivitiesModels.organization_id == organization_id)
        )
        activities = session.execute(activities_query).scalars().all()

        response = {
            'id': str(org.id),
            'name': org.name,
            'building': {
                'id': str(building.id),
                'address': building.address,
                'latitude_longitude': building.latitude_longitude
            },
            'phones': phones,
            'activities': activities
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail='Не удалось выполнить чтение из БД')
    
@router.get('/org_by_activity_tree')
def get_organizations_by_activity_tree(
    activity_name: str = Query(..., description="Название вида деятельности на первом уровне дерева"),
    session: Session = Depends(get_db)
):
    try:
        ActivityParent = aliased(ActivitiesModels, name='parent')
        ActivityChild = aliased(ActivitiesModels, name='child')
        
        activity_hierarchy = (
            select(ActivityParent.id)
            .where(ActivityParent.name == activity_name)
            .where(ActivityParent.parent_id.is_(None))
            .cte(recursive=True, name='activity_hierarchy')
        )
        
        activity_hierarchy_union = activity_hierarchy.union_all(
            select(ActivityChild.id)
            .select_from(ActivityChild)
            .join(activity_hierarchy, ActivityChild.parent_id == activity_hierarchy.c.id)
        )
        
        all_activity_ids = select(activity_hierarchy_union.c.id)
        
        organizations_query = (
            select(
                OrganizationsModels.id,
                OrganizationsModels.name,
                BuildingsModel.address,
                ActivitiesModels.name.label('activity_name')
            )
            .select_from(OrganizationsModels)
            .join(OrganizationActivitiesModels, OrganizationsModels.id == OrganizationActivitiesModels.organization_id)
            .join(ActivitiesModels, OrganizationActivitiesModels.activity_id == ActivitiesModels.id)
            .join(BuildingsModel, OrganizationsModels.buildings_id == BuildingsModel.id)
            .where(ActivitiesModels.id.in_(all_activity_ids))
            .order_by(OrganizationsModels.name, ActivitiesModels.name)
        )
        
        result = session.execute(organizations_query).all()
        
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"Вид деятельности '{activity_name}' не найден или не имеет дочерних элементов"
            )
        
        organizations_dict = {}
        for org_id, org_name, address, activity_name in result:
            if org_id not in organizations_dict:
                organizations_dict[org_id] = {
                    'id': str(org_id),
                    'name': org_name,
                    'address': address,
                    'activities': []
                }
            organizations_dict[org_id]['activities'].append(activity_name)
        
        response = list(organizations_dict.values())
        
        return {
            'search_activity': activity_name,
            'count': len(response),
            'organizations': response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail='Не удалось выполнить поиск по дереву видов деятельности')

@router.get('/activity_tree')
def get_activity_tree(
    parent_name: Optional[str] = Query(None, description="Название родительского вида деятельности"),
    session: Session = Depends(get_db)
):
    try:
        if parent_name:
            parent_activity = session.execute(
                select(ActivitiesModels).where(
                    ActivitiesModels.name == parent_name, 
                    ActivitiesModels.parent_id.is_(None)
                )
            ).scalar_one_or_none()
            
            if not parent_activity:
                raise HTTPException(status_code=404, detail="Родительский вид деятельности не найден")
            
            ParentActivity = aliased(ActivitiesModels, name='parent')
            ChildActivity = aliased(ActivitiesModels, name='child')
            
            activity_tree = (
                select(ParentActivity.id, ParentActivity.name, ParentActivity.parent_id)
                .where(ParentActivity.id == parent_activity.id)
                .cte(recursive=True, name='activity_tree')
            )
            
            activity_tree_union = activity_tree.union_all(
                select(ChildActivity.id, ChildActivity.name, ChildActivity.parent_id)
                .select_from(ChildActivity)
                .join(activity_tree, ChildActivity.parent_id == activity_tree.c.id)
            )
            
            tree_result = session.execute(
                select(activity_tree_union.c.id, activity_tree_union.c.name, activity_tree_union.c.parent_id)
                .order_by(activity_tree_union.c.name)
            ).all()
            
            return {
                'parent_activity': parent_name,
                'tree': [{'id': str(row.id), 'name': row.name, 'parent_id': str(row.parent_id) if row.parent_id else None} 
                        for row in tree_result]
            }
        else:
            root_activities = session.execute(
                select(ActivitiesModels).where(ActivitiesModels.parent_id.is_(None))
                .order_by(ActivitiesModels.name)
            ).scalars().all()
            
            return {
                'root_activities': [{'id': str(act.id), 'name': act.name} for act in root_activities]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail='Не удалось получить дерево видов деятельности')
    
@router.get('/organization/search')
def search_organizations_by_name(
    name: str = Query(..., description="Название организации для поиска"),
    limit: int = Query(100, description="Максимальное количество результатов"),
    session: Session = Depends(get_db)
):
    try:
        query = (
            select(OrganizationsModels, BuildingsModel)
            .join(BuildingsModel, OrganizationsModels.buildings_id == BuildingsModel.id)
            .where(OrganizationsModels.name.ilike(f"%{name}%"))
            .limit(limit)
        )
        
        results = session.execute(query).all()
        
        organizations_list = []
        for org, building in results:
            phones_query = select(OrganizationPhonesModels.phone_number).where(
                OrganizationPhonesModels.organization_id == org.id
            )
            phones = session.execute(phones_query).scalars().all()
            
            activities_query = (
                select(ActivitiesModels.name)
                .select_from(OrganizationActivitiesModels)
                .join(ActivitiesModels, OrganizationActivitiesModels.activity_id == ActivitiesModels.id)
                .where(OrganizationActivitiesModels.organization_id == org.id)
            )
            activities = session.execute(activities_query).scalars().all()
            
            organization_data = {
                'id': str(org.id),
                'name': org.name,
                'building': {
                    'id': str(building.id),
                    'address': building.address,
                    'latitude_longitude': building.latitude_longitude
                },
                'phones': phones,
                'activities': activities
            }
            organizations_list.append(organization_data)
        
        return {
            'search_query': name,
            'count': len(organizations_list),
            'organizations': organizations_list
        }
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail='Не удалось выполнить поиск организаций')