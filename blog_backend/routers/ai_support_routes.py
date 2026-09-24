import re
from typing import Optional
from database import get_db
from fastapi import APIRouter, Depends, status
from models import ChatLog, User
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/ai-support", tags=["AI Support"])


class ChatRequest(BaseModel):
  message: str = Field(..., min_length=1, max_length=1000)


class ChatResponse(BaseModel):
  reply: str
  suggested_actions: Optional[list[str]] = []


def generate_ai_reply(prompt: str) -> tuple[str, list[str]]:
  text = prompt.lower()

  if re.search(r"\b(create|write|publish|new)\b.*\b(post|blog|article)\b", text):
    return (
        (
            "To create a new post, navigate to the **Create Post** page, enter"
            " your title, select tags, write the body, and click **Publish**."
        ),
        ["How to edit posts?", "Supported markdown syntax"],
    )

  if re.search(r"\b(edit|update|delete|remove)\b.*\b(post|blog)\b", text):
    return (
        (
            "You can manage your posts directly from the Author Dashboard."
            " Find your post under the breakdown list and select **Edit (✏️)**"
            " or **Delete (🗑️)**."
        ),
        ["How do views get counted?", "Can I restore deleted posts?"],
    )

  if re.search(r"\b(subscription|tier|plan|upgrade|pro|enterprise)\b", text):
    return (
        (
            "We offer **Free**, **Pro**, and **Enterprise** subscription plans."
            " Upgrades unlock unlimited reads, priority emails, and custom"
            " badge flair."
        ),
        ["How does billing work?", "Where can I get invoices?"],
    )

  if re.search(
      r"\b(billing|invoice|payment|receipt|charge|price|pay)\b", text
  ):
    return (
        (
            "Payments are securely processed. Tax PDF invoices are"
            " automatically generated and sent to your registered email after"
            " every successful payment."
        ),
        ["Upgrade subscription", "View billing history"],
    )

  if re.search(r"\b(analytics|stats|chart|views|likes|share|graph)\b", text):
    return (
        (
            "Your Author Dashboard displays real-time engagement: total posts,"
            " comments, likes, and views, along with engagement and interaction"
            " share charts."
        ),
        ["How often do stats refresh?", "What counts as a like?"],
    )

  if re.search(r"\b(profile|account|password|change name|email)\b", text):
    return (
        (
            "You can update your display name, author bio, password, and email"
            " alerts directly inside **Account Settings**."
        ),
        ["Change password", "Notification settings"],
    )

  return (
      (
          "I'm your Blog Platform AI Assistant! I can help you create or manage"
          " posts, explain subscription tiers, clarify billing, or interpret"
          " your analytics dashboard."
      ),
      ["How to create posts", "How subscriptions work", "Explain analytics"],
  )


# Accept both / and empty path so redirects don't break POST requests
@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def handle_support_chat(payload: ChatRequest, db: Session = Depends(get_db)):
  reply, suggestions = generate_ai_reply(payload.message)

  # Log the message to chat_logs
  log_entry = ChatLog(
      user_id=None,
      question=payload.message,
      ai_response=reply,
  )
  db.add(log_entry)
  db.commit()

  return ChatResponse(reply=reply, suggested_actions=suggestions)