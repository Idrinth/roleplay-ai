from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app, CollectorRegistry
import re
import time
import os
from starlette.requests import Request

app = FastAPI(root_path="/api/v1", title="Gamemaster AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("UI_HOST", "http://localhost")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUEST_COUNT = Counter('app_http_request_total', 'Total HTTP Requests', ['method', 'status', 'path'])
REQUEST_LATENCY = Histogram('app_http_request_duration_seconds', 'HTTP Request Duration', ['method', 'status', 'path'])
REQUEST_IN_PROGRESS = Gauge('app_http_requests_in_progress', 'HTTP Requests in progress', ['method', 'path'])
registry = CollectorRegistry()
registry.register(REQUEST_COUNT)
registry.register(REQUEST_LATENCY)
registry.register(REQUEST_IN_PROGRESS)

app.mount("/metrics/", make_asgi_app(registry))

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    method = request.method
    path = re.sub(
        r"/[a-f0-9]{24}$",
        "/{id}",
        re.sub(
            r"/[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}(/|$)",
            r"/{uuid}\1",
            request.url.path,
            flags=re.IGNORECASE
        ),
        flags=re.IGNORECASE
    )
    REQUEST_IN_PROGRESS.labels(method=method, path=path).inc()
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    status = response.status_code
    REQUEST_COUNT.labels(method=method, status=status, path=path).inc()
    REQUEST_LATENCY.labels(method=method, status=status, path=path).observe(duration)
    REQUEST_IN_PROGRESS.labels(method=method, path=path).dec()

    return response
