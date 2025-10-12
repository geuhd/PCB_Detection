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


@app.get("/")
def root():
    return {"message": "PCB DETECTION API"}

@app.post("/detections", status_code=status.HTTP_201_CREATED, response_model = schemas.DetectCreate)
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
        title=title or file.filename,
        path_original= f"{IMAGEDIR}{file.filename}",                           
        path=path,
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
async def read_one_image_file(id: int,
        db:  Session= Depends(get_db)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post=post_query.first() 
    if post==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id: {id} was not found")
    print(post)

    return post

#delete a pcb image with the give id
#anyone can delete for now. 
@app.delete("/detections/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int,
                db:  Session= Depends(get_db)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post=post_query.first() 

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id: {id} does not exist")
    post_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
