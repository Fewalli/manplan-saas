from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(
    title="ManPlan API",
    description="API do ManPlan SaaS",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router, prefix="/api/v1")