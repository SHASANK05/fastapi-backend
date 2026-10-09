from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
import models

# Fraud Guard Limits
VELOCITY_WINDOW_MINUTES = 2
MAX_TXN_COUNT_IN_WINDOW = 3
DAILY_SPEND_LIMIT_INR = 100000.0
HIGH_VALUE_THRESHOLD_INR = 50000.0


class FraudEvaluationResult:
    def __init__(self, is_allowed: bool, status: str, reason: str = None):
        self.is_allowed = is_allowed
        self.status = status  # SUCCESS, FAILED, FLAGGED_FRAUD
        self.reason = reason


def evaluate_transaction_risk(
    db: Session,
    card_id: int,
    user_id: int,
    amount: float,
    cvv: str,
) -> FraudEvaluationResult:
    # Rule 1: CVV check (mock bank rejection)
    if cvv == "000":
        return FraudEvaluationResult(
            is_allowed=False,
            status="FAILED",
            reason="Payment rejected: Invalid CVV / Bank authorization failed."
        )

    # Rule 2: Single-ticket extreme threshold
    if amount > HIGH_VALUE_THRESHOLD_INR:
        return FraudEvaluationResult(
            is_allowed=False,
            status="FLAGGED_FRAUD",
            reason=f"Transaction limit exceeded: Max single transaction allowed is ₹{HIGH_VALUE_THRESHOLD_INR:,.0f}."
        )

    now = datetime.now(timezone.utc)

    # Rule 3: Velocity Check (Burst attempts within window)
    window_start = now - timedelta(minutes=VELOCITY_WINDOW_MINUTES)
    recent_txn_count = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.card_id == card_id,
            models.Transaction.created_at >= window_start
        )
        .count()
    )

    if recent_txn_count >= MAX_TXN_COUNT_IN_WINDOW:
        return FraudEvaluationResult(
            is_allowed=False,
            status="FLAGGED_FRAUD",
            reason=f"Velocity limit exceeded: Exceeded {MAX_TXN_COUNT_IN_WINDOW} attempts in {VELOCITY_WINDOW_MINUTES} minutes."
        )

    # Rule 4: Rolling 24-hour total spend volume
    day_start = now - timedelta(hours=24)
    daily_spent = (
        db.query(func.coalesce(func.sum(models.Transaction.amount), 0.0))
        .filter(
            models.Transaction.card_id == card_id,
            models.Transaction.status == "SUCCESS",
            models.Transaction.created_at >= day_start
        )
        .scalar()
    )

    if (daily_spent + amount) > DAILY_SPEND_LIMIT_INR:
        return FraudEvaluationResult(
            is_allowed=False,
            status="FLAGGED_FRAUD",
            reason=f"Daily spend limit of ₹{DAILY_SPEND_LIMIT_INR:,.0f} exceeded. (Current 24h spend: ₹{daily_spent:,.2f})."
        )

    # All checks passed
    return FraudEvaluationResult(is_allowed=True, status="SUCCESS", reason=None)
