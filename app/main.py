from fastapi import FastAPI, Depends
from . import models
from .database import engine, SessionLocal
from .routers import detections, users, auth, restore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from datetime import datetime, timezone , timedelta
from .utils import del_file


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


@scheduler.scheduled_job('interval', days=1)
async def purge():
    #Cant use the Depends session in a function that does not have Fast API decorator... 
    # Git hub thread "https://github.com/fastapi/fastapi/issues/1693#issuecomment-665833384" used for clarification
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

    deleted_at= datetime.utcnow()-timedelta(days=30)
    post_query = db.query(models.Post).filter(models.Post.deleted_at<=deleted_at).all()
    if len(post_query) > 0:
        for post in post_query:
            
            del_file(post.path)
            del_file(post.path_original)
            db.delete(post)
            db.commit()
            print(f"files for date {deleted_at} deleted")
    print(f"No files expired on {deleted_at}")