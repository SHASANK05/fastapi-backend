from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
import os
import uuid
import math

from database import get_db
import models, schemas, security

router = APIRouter(prefix="/posts", tags=["Posts"])
UPLOAD_DIR = "media/posts"

def save_uploaded_image(file: UploadFile, request: Request) -> str:
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/media/posts/{unique_filename}"

# 1. Search & Paginated Feed
@router.get("", response_model=schemas.PaginatedPostsResponse)
def get_posts(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search keyword in title or content"),
    db: Session = Depends(get_db)
):
    query = db.query(models.Post)

    # Search filter
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                models.Post.title.ilike(search_filter),
                models.Post.content.ilike(search_filter)
            )
        )

    total_count = query.count()
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

    # Pagination offset/limit
    posts = (
        query.order_by(models.Post.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    for p in posts:
        p.likes_count = len(p.likes)

    return {
        "total_count": total_count,
        "total_pages": total_pages,
        "current_page": page,
        "limit": limit,
        "posts": posts
    }

# 2. Get Mine
@router.get("/mine", response_model=list[schemas.PostOut])
def get_my_posts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    posts = db.query(models.Post).filter(models.Post.author_id == current_user.id).all()
    for p in posts:
        p.likes_count = len(p.likes)
    return posts

# 3. Get Single Post
@router.get("/{post_id}", response_model=schemas.PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.likes_count = len(post.likes)
    return post

# 4. Create Post with Image Upload
@router.post("", response_model=schemas.PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    image_url = None
    if image and image.filename:
        image_url = save_uploaded_image(image, request)

    new_post = models.Post(
        title=title,
        content=content,
        image_url=image_url,
        author_id=current_user.id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    new_post.likes_count = 0
    return new_post

# 5. Update Post (Text and/or Image)
@router.put("/{post_id}", response_model=schemas.PostOut)
def update_post(
    post_id: int,
    request: Request,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this post")

    if title is not None:
        post.title = title
    if content is not None:
        post.content = content
    if image and image.filename:
        post.image_url = save_uploaded_image(image, request)

    db.commit()
    db.refresh(post)
    post.likes_count = len(post.likes)
    return post

# 6. Delete Post
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post")

    db.delete(post)
    db.commit()
    return None