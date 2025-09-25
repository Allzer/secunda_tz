from fastapi import APIRouter


router = APIRouter(
    prefix="/v1/secunda",
    tags=["clients"]
)

@router.get('/')
def get_builds(builds_name):
    '''список всех организаций находящихся в конкретном здании'''

    return 'good'