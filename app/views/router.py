from fastapi import APIRouter

from app.views.pages import account, criteria, filters, login, media, root, sources, user, videos

views_router = APIRouter(include_in_schema=False)
views_router.include_router(root.router, tags=["Views"])
views_router.include_router(sources.router, tags=["Sources"])
views_router.include_router(videos.router, tags=["Videos"])
views_router.include_router(login.router, tags=["Logins"])
views_router.include_router(filters.router, tags=["Filters"])
views_router.include_router(criteria.router, tags=["Criteria"])
views_router.include_router(account.router, prefix="/account", tags=["Account"])
views_router.include_router(user.router, prefix="/user", tags=["Users"])
views_router.include_router(media.router, prefix="/media", tags=["Media"])
