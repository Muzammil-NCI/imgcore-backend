import os
import time
from typing import Optional, Tuple

from aws_embedded_metrics import metric_scope


def _env(name: str, default: str) -> str:
    v = os.getenv(name)
    return v if v not in (None, "") else default


def _resolve_route_template(request) -> str:
    # Prefer a low-cardinality route template (e.g. "/transform") vs raw path.
    route = request.scope.get("route")
    path_template = getattr(route, "path", None)
    if isinstance(path_template, str) and path_template:
        return path_template
    return request.url.path or "unknown"


def _common_dimensions(request, status_code: int) -> dict:
    return {
        "Service": _env("SERVICE_NAME", "ImageCore"),
        "Stage": _env("STAGE", _env("ENV", "dev")),
        "FunctionName": _env("AWS_LAMBDA_FUNCTION_NAME", "imgcore-function"),
        "Method": request.method,
        "Route": _resolve_route_template(request),
        "StatusCode": str(status_code),
    }


@metric_scope
def put_request_metrics(
    metrics,
    *,
    request,
    status_code: int,
    duration_ms: float,
    is_cold_start: bool,
    content_length_bytes: Optional[int] = None,
) -> None:
    namespace = _env("METRICS_NAMESPACE", "ImageCore")
    metrics.set_namespace(namespace)
    metrics.set_dimensions(_common_dimensions(request, status_code))

    # Core SLO-style metrics
    metrics.put_metric("Requests", 1, "Count")
    metrics.put_metric("Latency", duration_ms, "Milliseconds")

    # Status buckets for quick dashboards/alarms
    if 200 <= status_code <= 299:
        metrics.put_metric("2xx", 1, "Count")
    elif 400 <= status_code <= 499:
        metrics.put_metric("4xx", 1, "Count")
        metrics.put_metric("Errors", 1, "Count")
    elif 500 <= status_code <= 599:
        metrics.put_metric("5xx", 1, "Count")
        metrics.put_metric("Errors", 1, "Count")
    else:
        metrics.put_metric("OtherStatus", 1, "Count")

    if is_cold_start:
        metrics.put_metric("ColdStart", 1, "Count")

    if content_length_bytes is not None:
        metrics.put_metric("ResponseBytes", float(content_length_bytes), "Bytes")


def now_ms() -> float:
    return time.perf_counter() * 1000.0


def duration_ms(start_ms: float, end_ms: float) -> float:
    return max(0.0, end_ms - start_ms)


def clamp_dashboard_route(route: str) -> Tuple[str, bool]:
    # Guardrail in case any path leaks through as high-cardinality.
    # Returns (normalized_route, was_clamped).
    if not route or route == "unknown":
        return "unknown", False
    if len(route) > 200:
        return route[:200], True
    return route, False

