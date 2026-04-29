"""
Audit Service – V3
==================
Write immutable audit log entries for any state-changing operation.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log_action(
    db: Session,
    action_type: str,
    actor_user_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    old_value: dict | None = None,
    new_value: dict | None = None,
    description: str | None = None,
) -> AuditLog:
    """
    Persist an audit log entry and flush (but don't commit – let the caller commit).
    """
    entry = AuditLog(
        actor_user_id=actor_user_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value_json=json.dumps(old_value) if old_value else None,
        new_value_json=json.dumps(new_value) if new_value else None,
        description=description,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.flush()
    return entry
