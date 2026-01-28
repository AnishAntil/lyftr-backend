from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import hmac, hashlib, time, re
from .config import WEBHOOK_SECRET
from .models import init_db, get_db
from .storage import insert_message
from .logging_utils import log_request
from .metrics import http_requests, webhook_results, render_metrics


app = FastAPI()

@app.on_event("startup")
def startup():
    if not WEBHOOK_SECRET:
        raise RuntimeError("WEBHOOK_SECRET not set")
    init_db()

class WebhookMsg(BaseModel):
    message_id: str
    from_: str = Field(alias="from")
    to: str
    ts: str
    text: Optional[str] = Field(max_length=4096)

    @staticmethod
    def validate_msisdn(v):
        return re.match(r"^\+\d+$", v)

@app.post("/webhook")
async def webhook(req: Request):
    start = time.time()
    body = await req.body()
    sig = req.headers.get("X-Signature")

    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not sig or not hmac.compare_digest(sig, expected):
        webhook_results["invalid_signature"] += 1
        log_request(req, 401, start, {"result": "invalid_signature"})
        raise HTTPException(401, detail="invalid signature")

    payload = await req.json()
    msg = WebhookMsg(**payload)

    result = insert_message(payload)
    webhook_results[result] += 1

    log_request(req, 200, start, {
        "message_id": payload["message_id"],
        "dup": result == "duplicate",
        "result": result
    })

    return {"status": "ok"}

@app.get("/messages")
def messages(limit: int = 50, offset: int = 0,
             from_: Optional[str] = None,
             since: Optional[str] = None,
             q: Optional[str] = None):
    db = get_db()
    where, params = [], []

    if from_:
        where.append("from_msisdn=?")
        params.append(from_)
    if since:
        where.append("ts>=?")
        params.append(since)
    if q:
        where.append("LOWER(text) LIKE ?")
        params.append(f"%{q.lower()}%")

    clause = "WHERE " + " AND ".join(where) if where else ""
    total = db.execute(f"SELECT COUNT(*) FROM messages {clause}", params).fetchone()[0]

    rows = db.execute(
        f"""SELECT * FROM messages {clause}
            ORDER BY ts ASC, message_id ASC
            LIMIT ? OFFSET ?""",
        (*params, limit, offset)
    ).fetchall()

    return {
        "data": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/stats")
def stats():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    senders = db.execute("""
        SELECT from_msisdn as from, COUNT(*) as count
        FROM messages GROUP BY from_msisdn
        ORDER BY count DESC LIMIT 10
    """).fetchall()

    ts = db.execute("SELECT MIN(ts), MAX(ts) FROM messages").fetchone()

    return {
        "total_messages": total,
        "senders_count": len(senders),
        "messages_per_sender": [dict(r) for r in senders],
        "first_message_ts": ts[0],
        "last_message_ts": ts[1]
    }

@app.get("/health/live")
def live():
    return {"status": "ok"}

@app.get("/health/ready")
def ready():
    try:
        get_db().execute("SELECT 1")
        return {"status": "ok"}
    except:
        raise HTTPException(503)

@app.get("/metrics")
def metrics():
    return render_metrics()
