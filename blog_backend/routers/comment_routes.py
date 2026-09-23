if post.author_id != current_user.id:
    new_notif = Notification(
        recipient_id=post.author_id,
        actor_id=current_user.id,
        notification_type="comment",
        message=f"{current_user.username} commented on '{post.title[:30]}...'"
    )
    db.add(new_notif)
    db.commit()