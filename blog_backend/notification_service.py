from datetime import datetime
from fastapi import BackgroundTasks
from email_service import send_smtp_email

def dispatch_post_activity_notification(
    background_tasks: BackgroundTasks,
    recipient_email: str,
    recipient_username: str,
    actor_username: str,
    post_title: str,
    activity_type: str,
    comment_text: str = None
):
    """Constructs the notification and registers it with FastAPI BackgroundTasks."""
    if not recipient_email:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    subject = f"New Activity on your post: '{post_title}'"

    comment_line = f"\nComment: \"{comment_text}\"" if comment_text else ""
    body_text = (
        f"Hi {recipient_username},\n\n"
        f"Post: “{post_title}”\n"
        f"User: {actor_username}\n"
        f"Activity: {activity_type} your post{comment_line}\n"
        f"Time: {timestamp}\n\n"
        f"Best regards,\nBlog Management Platform"
    )

    body_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #222;">
        <h3>Hello {recipient_username},</h3>
        <p>There is new activity on your blog post:</p>
        <div style="background-color: #f4f6f8; border-left: 4px solid #007bff; padding: 14px; margin: 16px 0; border-radius: 4px;">
          <p style="margin: 4px 0;"><strong>Post:</strong> “{post_title}”</p>
          <p style="margin: 4px 0;"><strong>User:</strong> {actor_username}</p>
          <p style="margin: 4px 0;"><strong>Activity:</strong> {activity_type} your post</p>
          {f'<p style="margin: 4px 0;"><strong>Comment:</strong> <em>"{comment_text}"</em></p>' if comment_text else ''}
          <p style="margin: 4px 0;"><strong>Time:</strong> {timestamp}</p>
        </div>
        <p>Keep engaging with your readers!</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;" />
        <p style="font-size: 12px; color: #888;">Blog Management Platform Automated Notifications</p>
      </body>
    </html>
    """

    background_tasks.add_task(
        send_smtp_email,
        to_email=recipient_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html
    )