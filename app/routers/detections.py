from fastapi import FastAPI, File, UploadFile, Form,Response, status, HTTPException,Depends,APIRouter, BackgroundTasks
from random import randint
from fastapi.responses import FileResponse
import os
import pathlib
from typing import Union
import uuid
from .. import schemas, models
from sqlalchemy.orm import Session
from ..database import engine, get_db
from sqlalchemy import func
from .. import oauth2

def del_file(path):
    pathlib.Path(path).unlink(missing_ok=False)
    print("file delected")
        
router = APIRouter(
    prefix="/detections",
    tags=['Detections']
)

IMAGEDIR = "images/"
IMAGEDIR_PROC = "images_processed/"


@router.post("/", status_code=status.HTTP_201_CREATED, response_model = schemas.DetectCreate)
async def idetect(title: str | None = Form(None),
                published: bool = Form(True),
                file: UploadFile= File(...),
                db:  Session= Depends(get_db),
                current_user: int = Depends(oauth2.get_current_user)):
    
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

@router.get("/")
async def readall_image_file():

    #get image file
    files =os.listdir(IMAGEDIR_PROC)

    path = 1
    

    return FileResponse(path)

@router.get("/{id}")
async def read_one_image_file(id: int,
        db:  Session= Depends(get_db),
        current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post=post_query.first() 
    if post==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id: {id} was not found")
    print(post)

    return post

#delete a pcb image with the give id
#anyone can delete for now. 
@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int,
                background_tasks: BackgroundTasks,
                db:  Session= Depends(get_db),
                current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post=post_query.first() 
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id: {id} does not exist")
    path=post.path
    print(path)

    background_tasks.add_task(del_file,post.path_original)
    post_query.delete(synchronize_session=False)
    db.commit()
    background_tasks.add_task(del_file,path)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
