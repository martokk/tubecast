from fastapi import APIRouter

from tubecast.views.endpoints import feeds, media, sources

views_router = APIRouter()
views_router.include_router(sources.router, tags=["Views"])
views_router.include_router(feeds.router, prefix="/feed", tags=["Feed"])
views_router.include_router(media.router, prefix="/media", tags=["Media"])
