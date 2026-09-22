from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import User, Post, Like, Comment
from security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["User Dashboard"])

@router.get("/stats", status_code=status.HTTP_200_OK)
def get_user_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns aggregated metrics for the authenticated user and 
    per-post breakdown formatted for Chart.js visualization.
    """
    user_id = current_user.id

    # 1. Total Posts Created by User
    total_posts = db.query(func.count(Post.id)).filter(Post.author_id == user_id).scalar() or 0

    # 2. Total Comments Made by User
    total_comments_made = db.query(func.count(Comment.id)).filter(Comment.user_id == user_id).scalar() or 0

    # 3. User's Posts IDs
    user_posts = db.query(Post).filter(Post.author_id == user_id).all()
    user_post_ids = [p.id for p in user_posts]

    # 4. Total Likes Received on User's Posts
    if user_post_ids:
        total_likes_received = (
            db.query(func.count(Like.id))
            .filter(Like.post_id.in_(user_post_ids))
            .scalar() or 0
        )
        total_views = sum(getattr(p, "views", 0) for p in user_posts)
    else:
        total_likes_received = 0
        total_views = 0

    # 5. Chart Data: Breakdown per post (Title, Likes, Comments, Views)
    posts_breakdown = []
    for post in user_posts:
        like_count = len(post.likes)
        comment_count = len(post.comments)
        posts_breakdown.append({
            "post_id": post.id,
            "title": post.title[:20] + "..." if len(post.title) > 20 else post.title,
            "likes": like_count,
            "comments": comment_count,
            "views": getattr(post, "views", 0)
        })

    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        },
        "overview": {
            "total_posts": total_posts,
            "total_comments_made": total_comments_made,
            "total_likes_received": total_likes_received,
            "total_views": total_views
        },
        "posts_breakdown": posts_breakdown
    }