from fastapi import APIRouter
from app.modules.controls import routes as controls_routes
from app.modules.documents import routes as documents_routes
from app.modules.tabular import routes as tabular_routes
from app.modules.ai_responses import routes as ai_routes

api_router = APIRouter()

# Include module routers
api_router.include_router(
    controls_routes.router,
    prefix="/controls",
    tags=["controls"]
)

api_router.include_router(
    documents_routes.router,
    prefix="/documents",
    tags=["documents"]
)

api_router.include_router(
    tabular_routes.router,
    prefix="/tabular",
    tags=["tabular-view"]
)

api_router.include_router(
    ai_routes.router,
    prefix="/ai",
    tags=["ai-responses"]
) 