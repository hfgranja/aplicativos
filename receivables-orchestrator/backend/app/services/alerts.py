from __future__ import annotations

from sqlalchemy.orm import Session

from app import models


def raise_alert(db: Session, *, merchant_id: str | None, severity: str, category: str,
                 message: str, context: dict | None = None) -> models.Alert:
    alert = models.Alert(
        merchant_id=merchant_id,
        severity=severity,
        category=category,
        message=message,
        context=context or {},
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
