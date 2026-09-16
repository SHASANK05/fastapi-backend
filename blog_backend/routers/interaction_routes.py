from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, security
from email_service import send_notification_email

router = APIRouter(prefix="/posts/{post_id}", tags=["Comments & Likes"])

@router.post("/comments", response_model=schemas.CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    post_id: int,
    comment_data: schemas.CommentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    new_comment = models.Comment(
        post_id=post.id,
        user_id=current_user.id,
        text=comment_data.text
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    if post.author_id != current_user.id:
        subject = f"New comment on your post '{post.title}'"
        body = f"User @{current_user.username} commented: '{new_comment.text}'"
        background_tasks.add_task(send_notification_email, post.author.email, subject, body)

    return new_comment

@router.post("/like")
def toggle_like_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing_like = db.query(models.Like).filter(
        models.Like.post_id == post.id,
        models.Like.user_id == current_user.id
    ).first()

    if existing_like:
        db.delete(existing_like)
        db.commit()
        return {"detail": "Post unliked", "liked": False}
    else:
        new_like = models.Like(post_id=post.id, user_id=current_user.id)
        db.add(new_like)
        db.commit()

        if post.author_id != current_user.id:
            subject = f"New like on your post '{post.title}'"
            body = f"User @{current_user.username} liked your post!"
            background_tasks.add_task(send_notification_email, post.author.email, subject, body)

        return {"detail": "Post liked", "liked": True}