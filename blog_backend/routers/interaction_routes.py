from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
from models import User, Post, Like, Comment, Notification
from security import get_current_user
from notification_service import dispatch_post_activity_notification

router = APIRouter(prefix="/interactions", tags=["Interactions"])


class CommentCreate(BaseModel):
    comment_text: str = Field(..., min_length=1, description="Text content of the comment")


@router.post("/posts/{post_id}/like", status_code=status.HTTP_200_OK)
def like_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    existing_like = (
        db.query(Like)
        .filter(Like.post_id == post_id, Like.user_id == current_user.id)
        .first()
    )
    if existing_like:
        db.delete(existing_like)
        db.commit()
        return {"message": "Post unliked"}

    new_like = Like(post_id=post_id, user_id=current_user.id)
    db.add(new_like)

    # In-App Notification trigger: Notify author if someone else liked the post
    if post.author_id != current_user.id:
        in_app_notif = Notification(
            recipient_id=post.author_id,
            actor_id=current_user.id,
            notification_type="like",
            message=f"{current_user.username} liked your post '{post.title[:30]}...'"
        )
        db.add(in_app_notif)

    db.commit()

    # Trigger background email notification if someone else liked the post
    post_author = post.author or db.query(User).filter(User.id == post.author_id).first()
    if post_author and post_author.id != current_user.id:
        dispatch_post_activity_notification(
            background_tasks=background_tasks,
            recipient_email=post_author.email,
            recipient_username=post_author.username,
            actor_username=current_user.username,
            post_title=post.title,
            activity_type="Liked",
        )

    return {"message": "Post liked"}


@router.post("/posts/{post_id}/comment", status_code=status.HTTP_201_CREATED)
def comment_post(
    post_id: int,
    comment_in: CommentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    new_comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        text=comment_in.comment_text,
    )
    db.add(new_comment)

    # In-App Notification trigger: Notify author if someone else commented
    if post.author_id != current_user.id:
        in_app_notif = Notification(
            recipient_id=post.author_id,
            actor_id=current_user.id,
            notification_type="comment",
            message=f"{current_user.username} commented on '{post.title[:30]}...'"
        )
        db.add(in_app_notif)

    db.commit()
    db.refresh(new_comment)

    # Trigger background email notification if someone else commented on the post
    post_author = post.author or db.query(User).filter(User.id == post.author_id).first()
    if post_author and post_author.id != current_user.id:
        dispatch_post_activity_notification(
            background_tasks=background_tasks,
            recipient_email=post_author.email,
            recipient_username=post_author.username,
            actor_username=current_user.username,
            post_title=post.title,
            activity_type="Commented on",
            comment_text=comment_in.comment_text,
        )

    return {"message": "Comment added successfully", "comment_id": new_comment.id}