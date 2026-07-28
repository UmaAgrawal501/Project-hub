from fastapi import APIRouter

from app.api.v1 import auth, draft, projects, public, share, versions

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(draft.router)
api_router.include_router(versions.router)
api_router.include_router(share.router)
api_router.include_router(public.router)


@api_router.get("/health")
def health() -> dict:
    return {"data": {"status": "ok"}}
