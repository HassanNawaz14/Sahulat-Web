from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.bills import router as bills_router
from app.api.v1.consumption import router as consumption_router
from app.jobs.cron_definitions import start_scheduler

app = FastAPI(title="Sahulat API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(bills_router)
app.include_router(consumption_router)


@app.on_event("startup")
async def startup():
    start_scheduler()


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
