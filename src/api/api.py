from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from src.models.models import BuildingsModel, OrganizationsModels


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