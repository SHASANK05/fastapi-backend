from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models import SubscriptionPlan, PlanType, PLAN_LIMITS, Post

LIMIT_MESSAGE = "You’ve reached your plan limit. Kindly upgrade your plan to continue."

def get_user_plan(db: Session, user_id: int) -> PlanType:
    """Retrieves the active subscription plan for a user, defaulting to Basic."""
    sub = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.user_id == user_id, 
        SubscriptionPlan.is_active == 1
    ).first()
    return sub.plan_name if sub else PlanType.BASIC

def check_post_creation_limit(db: Session, user_id: int, image_count: int = 1):
    """Checks if the user has reached their allowed post count or image upload limits."""
    plan = get_user_plan(db, user_id)
    limits = PLAN_LIMITS[plan]

    # Post count check
    current_posts = db.query(Post).filter(Post.author_id == user_id).count()
    if current_posts >= limits["max_posts"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=LIMIT_MESSAGE)

    # Image per post check
    if image_count > limits["max_images_per_post"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=LIMIT_MESSAGE)

def check_interaction_limit(db: Session, user_id: int, action_type: str, current_count: int):
    """Checks if the user has exceeded their like or comment allowances."""
    plan = get_user_plan(db, user_id)
    limits = PLAN_LIMITS[plan]

    limit_key = f"max_{action_type}"
    if current_count >= limits.get(limit_key, 0):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=LIMIT_MESSAGE)