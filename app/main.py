from fastapi import FastAPI, File, UploadFile, Form,Response, status, HTTPException,Depends
from random import randint
from fastapi.responses import FileResponse
import os
from typing import Union
import uuid
from pydantic import BaseModel
from datetime import datetime
from . import schemas, models
from sqlalchemy.orm import Session
from .database import engine, get_db
from sqlalchemy import func

models.Base.metadata.create_all(bind=engine)
IMAGEDIR = "images/"
IMAGEDIR_PROC = "images_processed/"

app = FastAPI()

posts =[]
class Post(BaseModel):
    title: str
    path: str
    published: bool = True
    id: int
    created_at: datetime


@app.get("/")
def root():
    return {"message": "PCB DETECTION API"}

@app.post("/detections", status_code=status.HTTP_201_CREATED, response_model = schemas.PostCreate)
async def idetect(title: str | None = Form(None),
                published: bool = Form(True),
                file: UploadFile= File(...),
                db:  Session= Depends(get_db)):
    
    print(title)
    file.filename = f"{uuid.uuid4()}.jpg"
    contents = await file.read()

    #save file
    with open(f"{IMAGEDIR}{file.filename}", "wb") as f:
        f.write(contents)


    #get image file
    with open(f"{IMAGEDIR_PROC}{file.filename}", "wb") as f:
        f.write(contents)

    path = f"{IMAGEDIR_PROC}{file.filename}"


    new_post = models.Post(
        title=title or file.filename,              # original name
        path=path,              # path to processed image
        published=published,        
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@app.get("/detections")
async def readall_image_file():

    #get image file
    files =os.listdir(IMAGEDIR_PROC)

    path = f"{IMAGEDIR_PROC}{files[random_index]}"
    

    return FileResponse(path)

@app.get("/detections/{id}")
async def read_one_image_file(id: int):
   files =os.listdir(IMAGEDIR_PROC)


   path = f"{IMAGEDIR_PROC}{files[id]}"

   return FileResponse(path)

@app.delete("/detections/{id}")
def delete_post(id: int):
    print("delete")

    return {"message": "deleted"}
