from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from app import models, schemas, oauth2
from app.database import get_db
from app.yolo.detector import run_yolo_detection
import aiofiles
import os
import uuid
from typing import Optional


router = APIRouter(prefix="/detections", tags=["Detections"])

import pathlib

# Use absolute paths based on the project root (one level above "app")
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
IMAGEDIR = str("images")
IMAGEDIR_PROC = str( "images_processed")

# Make sure folders exist
os.makedirs(IMAGEDIR, exist_ok=True)
os.makedirs(IMAGEDIR_PROC, exist_ok=True)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.DetectCreate)
async def idetect(
    title: str | None = Form(None),
    published: bool = Form(True),
    model_name: str = Form(..., description="YOLO model to use: v3, v8m, or v8n"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    """
    Upload image -> stream in chunks -> run YOLO detection -> 
    save processed image -> store result in DB.
    """

    print(f"⚙️ Running detection: Title={title}, Model={model_name}")

    # 1️⃣ Generate unique filenames
    new_filename = f"{uuid.uuid4()}.jpg"
    original_path = os.path.join(IMAGEDIR, new_filename)
    processed_path = os.path.join(IMAGEDIR_PROC, new_filename)

    # 2️⃣ Stream file in chunks asynchronously
    CHUNK_SIZE = 1024 * 1024  # 1MB per chunk
    try:
        async with aiofiles.open(original_path, "wb") as buffer:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                await buffer.write(chunk)
    except Exception as e:
        print(f"❌ File save error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file due to streaming error."
        )
    finally:
        await file.close()

    # 3️⃣ Run YOLO detection (offloaded to threadpool)
    try:
        detection_result = await run_in_threadpool(
            run_yolo_detection,
            model_name=model_name,
            original_image_path=original_path,
            output_image_path=processed_path,
        )

        if not detection_result:
            raise Exception(f"YOLO detection failed for model '{model_name}'")

        print(f"✅ Detection complete for model: {model_name}")

    except Exception as e:
        print(f"❌ YOLO processing error: {e}")
        if os.path.exists(original_path):
            os.remove(original_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {e}"
        )

    # 4️⃣ Save detection record in DB
    new_post = models.Post(
        title=title or file.filename,
        path_original=original_path,
        path=processed_path,
        published=published,
        owner_id=current_user.id,
        model_name=model_name,  # optional if column added
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    print(f"📦 Record saved for user {current_user.id}")
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

