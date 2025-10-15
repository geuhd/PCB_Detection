from fastapi import FastAPI
from . import models
from .database import engine
from .routers import detections, users

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(detections.router)
app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "PCB DETECTION API"}

