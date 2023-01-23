from fastapi import APIRouter

from tubecast.api.v1.endpoints import login, source, users

api_router = APIRouter()

api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/user", tags=["Users"])
api_router.include_router(source.router, prefix="/source", tags=["sources"])
