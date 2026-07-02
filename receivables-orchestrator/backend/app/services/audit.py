"""Agente de Auditoria (secao 6/10/11): log imutavel com cadeia de hash.

Cada registro inclui o hash do registro anterior — qualquer adulteracao
retroativa quebra a cadeia e e detectavel por `verify_chain`.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app import models


def _compute_hash(prev_hash: Optional[str], actor: str, action: str, entity_type: str,
                   entity_id: str, before: Any, after: Any, timestamp: datetime) -> str:
    payload = json.dumps(
        {
            "prev_hash": prev_hash,
            "actor": actor,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "before": before,
            "after": after,
            "timestamp": timestamp.isoformat(),
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def record(db: Session, *, actor: str, action: str, entity_type: str, entity_id: str,
           before: Optional[dict] = None, after: Optional[dict] = None) -> models.AuditLog:
    last = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).first()
    prev_hash = last.hash if last else None
    timestamp = datetime.utcnow()
    entry_hash = _compute_hash(prev_hash, actor, action, entity_type, entity_id, before, after, timestamp)

    log = models.AuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before=before,
        after=after,
        timestamp=timestamp,
        prev_hash=prev_hash,
        hash=entry_hash,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def verify_chain(db: Session) -> bool:
    logs = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.asc()).all()
    prev_hash = None
    for log in logs:
        expected = _compute_hash(prev_hash, log.actor, log.action, log.entity_type, log.entity_id,
                                  log.before, log.after, log.timestamp)
        if expected != log.hash or log.prev_hash != prev_hash:
            return False
        prev_hash = log.hash
    return True
