# Lyftr AI Backend Assignment

Production-style FastAPI service for ingesting WhatsApp-like webhooks.

## Setup Used
VSCode + No AI Copilot used for generation (Manual Implementation based on strict PDF spec).

## How to Run

1. **Set Environment Variable:**
   ```bash
   export WEBHOOK_SECRET="testsecret"

2. Start Stack:

Bash
make up


The API will be available at http://localhost:8000.

Stop Stack:

Bash
make down
Endpoints
POST /webhook: Ingest message (Requires X-Signature).

GET /messages: List messages (Supports limit, offset, from, since, q).

GET /stats: Analytical stats.

GET /metrics: Prometheus metrics.

GET /health/live & /health/ready: K8s probes.

Design Decisions
HMAC Verification: Implemented manually using hashlib and hmac on the raw request body bytes before JSON parsing to ensure cryptographic accuracy.

Pagination: Standard LIMIT/OFFSET SQL approach. Returns a total count header/field calculated via a separate window-like COUNT(*) query for the specific filter set.

Stats/Metrics: * /stats: Calculated on-the-fly using SQL aggregations (efficient for SQLite < 1M rows).

/metrics: Uses prometheus-client to expose standard counters for request rates and webhook outcomes (created, duplicate, invalid).


Idempotency: Relies on SQLite PRIMARY KEY (message_id) constraint. The app catches IntegrityError and returns 200 OK (swallowing the error) to satisfy the "exactly once" ingestion requirement from the webhook provider's perspective.
