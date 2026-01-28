from datetime import datetime
from app.models import get_db

def insert_message(msg):
    db = get_db()
    try:
        db.execute("""
        INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)
        """, (
            msg["message_id"],
            msg["from"],
            msg["to"],
            msg["ts"],
            msg.get("text"),
            datetime.utcnow().isoformat() + "Z"
        ))
        db.commit()
        return "created"
    except Exception:
        return "duplicate"
