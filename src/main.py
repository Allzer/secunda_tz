from fastapi import FastAPI

from src.api.api import router as router

app = FastAPI()

app.include_router(router)

from src import api