from fastapi import FastAPI, Depends,Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from . import models
from .database import engine, SessionLocal
from .routers import detections, users, auth, restore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from datetime import datetime, timezone , timedelta
from .utils import del_file

# 1 GB max, adjust as needed
MAX_UPLOAD_SIZE = 1024 * 1024 * 5 # 100 MB example

class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if int(request.headers.get("content-length", 0)) > MAX_UPLOAD_SIZE:
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse("File too large", status_code=413)
        return await call_next(request)

models.Base.metadata.create_all(bind=engine)


scheduler = AsyncIOScheduler(timezone=utc)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
app.add_middleware(LimitUploadSizeMiddleware)
app.include_router(auth.router)
app.include_router(detections.router)
app.include_router(users.router)
app.include_router(restore.router)

@app.get("/")
def root():
    return {"message": "PCB DETECTION API"}

app.mount("/images", StaticFiles(directory="images"),name="images")
app.mount("/images_processed", StaticFiles(directory="images_processed"),name="images_processed")


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