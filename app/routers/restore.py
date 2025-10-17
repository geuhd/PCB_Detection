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


router = APIRouter(
    prefix="/restore",
    tags=['restore']
)

@router.post("/{id}")
def restore_detect(id: int,
        db:  Session= Depends(get_db)):
    
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post=post_query.first() 
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id: {id} does not exist")
    post.deleted= False
    post.deleted_at= None
    db.commit()
    return {"message": "restored features"}