import json, time, uuid, logging
from datetime import datetime

logger = logging.getLogger("app")
logging.basicConfig(level=logging.INFO)

def log_request(request, status, start, extra=None):
    payload = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "level": "INFO",
        "request_id": str(uuid.uuid4()),
        "method": request.method,
        "path": request.url.path,
        "status": status,
        "latency_ms": int((time.time() - start) * 1000)
    }
    if extra:
        payload.update(extra)
    logger.info(json.dumps(payload))
