from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from chem.routes import generate_router
from core.config_loader import settings

from auth.routes.auth_router import auth_router
from user.routes.user_router import user_router
from chem.routes.generate_router import router

from core.database import init_db

openapi_tags = [
    {
        "name": "Users",
        "description": "User operations",
    },
    {
        "name": "Chemistry",
        "description": "Molecule generation via NVIDIA",
    },
]

app = FastAPI(openapi_tags=openapi_tags)

@app.on_event("startup")
def on_startup():
    init_db()

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth_router, prefix='/api')
app.include_router(user_router, prefix='/api', tags=['Users'])
app.include_router(router, prefix='/api', tags=['Chemistry'])




