from fastapi import APIRouter


router = APIRouter(
    prefix="/v1/secunda",
    tags=["clients"]
)

@router.get('/')
def get_builds():
    return 'good'