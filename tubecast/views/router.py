from fastapi import APIRouter

from tubecast.views.endpoints import feeds, sources

views_router = APIRouter()
views_router.include_router(sources.router, tags=["Views"])
views_router.include_router(feeds.router, prefix="/feed", tags=["Feed"])
