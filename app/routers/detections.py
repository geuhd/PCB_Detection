from fastapi import FastAPI, File, UploadFile, Form,Response, status, HTTPException,Depends,APIRouter
from app.yolo_models import machine_models


from random import randint
from fastapi.responses import FileResponse
from typing import List, Optional,Union
import uuid
from .. import schemas, models
from sqlalchemy.orm import Session
from ..database import engine, get_db
from .. import oauth2
from datetime import datetime

import shutil # <-- New Import: Used for efficient file copying/streaming
import os     # <-- New Import: Used for directory creation
import aiofiles #



        
router = APIRouter(
    prefix="/detections",
    tags=['Detections']
)

IMAGEDIR = "images/"
IMAGEDIR_PROC = "images_processed/"






@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.DetectCreate)
async def idetect(
    title: str | None = Form(None),
    published: bool = Form(True),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    print(title)
    
    # 1. Generate new filename and paths
    new_filename = f"{uuid.uuid4()}.jpg"
    original_path = f"{IMAGEDIR}{new_filename}"
    processed_path = f"{IMAGEDIR_PROC}{new_filename}"
    
    # Define chunk size for streaming (e.g., 1MB)
    CHUNK_SIZE = 512 * 512 

    # 2. ASYNCHRONOUSLY STREAM THE FILE TO ITS ORIGINAL LOCATION (FIX)
    # This uses aiofiles and the native UploadFile stream for proper async I/O.
    try:
        # aiofiles.open ensures file writing is non-blocking
        async with aiofiles.open(original_path, "wb") as buffer:
            # Read from the UploadFile stream chunk by chunk
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                await buffer.write(chunk)
    except Exception as e:
        print(f"Error during asynchronous file streaming: {e}")
        # Re-raise as an HTTP Exception
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file due to streaming error."
        )
    finally:
        # The stream should be closed by the framework/context manager, 
        # but it is safe to keep this here if needed.
        # Removing explicit close if we switch to an async context manager, but since we are
        # using file.read() outside of a context manager, we must ensure it closes.
        await file.close()


    # 3. COPY THE SAVED FILE TO THE PROCESSED LOCATION
    # We still use shutil.copy2 since the file is now saved on disk.
    try:
        shutil.copy2(original_path,processed_path)
        # = machine_models.get_detect(original_path)
    except Exception as e:
        print(f"Error copying file for processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create processed copy of the file."
        )
    #processed_path=machine_models.get_detect(original_path,processed_path)


    # 4. Save to Database (Rest of your original logic)
    new_post = models.Post(
        title=title or file.filename,
        path_original=original_path,                         
        path=processed_path,
        published=published, 
        owner_id=current_user.id      
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@router.get("/")
async def get_all(db:  Session= Depends(get_db),
                    user_id:int=Depends(oauth2.get_current_user),
                    limit:int =10,
                    skip:int =0,
                    search: Optional[str]=""):
    print(user_id)
    posts1 = db.query(models.Post).group_by(models.Post.id).filter(models.Post.title.contains(search),
                                                                  models.Post.owner_id==user_id.id).limit(limit).offset(skip).all()
    posts2 = db.query(models.Post).group_by(models.Post.id).filter(models.Post.title.contains(search),
                                                                  models.Post.published==True).limit(limit).offset(skip).all()
    
    posts=posts1 +posts2
    
    return [{"post": post} for post in posts]

@router.get("/mine")
async def get_mine(db:  Session= Depends(get_db),
                    user_id:int=Depends(oauth2.get_current_user),
                    limit:int =10,
                    skip:int =0,
                    search: Optional[str]=""):
    print(user_id)
    posts = db.query(models.Post).group_by(models.Post.id).filter(models.Post.title.contains(search),
                                                                  models.Post.owner_id==user_id.id).limit(limit).offset(skip).all()

    
    return [{"post": post} for post in posts]

@router.get("/{id}")
async def read_one_image_file(id: int,
        db:  Session= Depends(get_db),
        current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post=post_query.first() 
    if post==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id: {id} was not found")
    
    if (post.owner_id != current_user.id) & (post.published == False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorised to perform action")
    print(post)

    return post

#delete a pcb image with the give id
#anyone can delete for now. 
@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int,
                db:  Session= Depends(get_db),
                current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post=post_query.first() 
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id: {id} does not exist")
    
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorised to perform action")
    
    post.deleted= True
    post.deleted_at= datetime.utcnow()
    db.commit()
    #path=post.path
    #print(path)
    #background_tasks.add_task(del_file,post.path_original)
    #post_query.delete(synchronize_session=False)
    #db.commit()
    #background_tasks.add_task(del_file,path)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

