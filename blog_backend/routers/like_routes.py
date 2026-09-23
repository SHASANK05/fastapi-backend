from models import Notification

# Trigger notification only if the liker is not the post author
if post.author_id != current_user.id:
    like_notif = Notification(
        recipient_id=post.author_id,
        actor_id=current_user.id,
        notification_type="like",
        message=f"{current_user.username} liked your post '{post.title[:30]}...'"
    )
    db.add(like_notif)

db.commit()