from fastapi import FastAPI, File, UploadFile, Form,Response, status, HTTPException,Depends,APIRouter
from random import randint
from fastapi.responses import FileResponse
import os
from typing import Union
import uuid
from .. import schemas, models
from sqlalchemy.orm import Session
from ..database import engine, get_db
from sqlalchemy import func
from .. import oauth2


router = APIRouter(
    prefix="/restore",
    tags=['restore']
)

@router.post("/{id}")
def restore_detect(id: int,
        db:  Session= Depends(get_db),
        current_user: int = Depends(oauth2.get_current_user)):
    
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post=post_query.first() 
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id: {id} does not exist")
    if (post.owner_id != current_user.id) & (post.published == False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorised to perform action")
    if (post.deleted is None) or post.deleted == False:
        #change code sent here
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"file aready restored or not deleted")
    post.deleted= False
    post.deleted_at= None
    db.commit()
    return post