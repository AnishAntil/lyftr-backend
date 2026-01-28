from collections import Counter

http_requests = Counter()
webhook_results = Counter()

def render_metrics():
    lines = []
    for (path, status), v in http_requests.items():
        lines.append(f'http_requests_total{{path="{path}",status="{status}"}} {v}')
    for result, v in webhook_results.items():
        lines.append(f'webhook_requests_total{{result="{result}"}} {v}')
    return "\n".join(lines)
