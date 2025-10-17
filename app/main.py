from fastapi import FastAPI
from . import models
from .database import engine
from .routers import detections, users, auth, restore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc
from contextlib import asynccontextmanager


models.Base.metadata.create_all(bind=engine)


scheduler = AsyncIOScheduler(timezone=utc)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(detections.router)
app.include_router(users.router)
app.include_router(restore.router)

@app.get("/")
def root():
    return {"message": "PCB DETECTION API"}

@scheduler.scheduled_job('interval', minutes=1)
async def purge():
    print("deleted values over 30 days")