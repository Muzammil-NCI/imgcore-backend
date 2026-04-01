import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from app import router
from app.observability.metrics import duration_ms, now_ms, put_request_metrics

logger = logging.getLogger(__name__)

app = FastAPI(title="ImageCore API", description="API for image transformation and processing")

_COLD_START = True


@app.middleware("http")
async def cloudwatch_metrics_middleware(request, call_next):
    global _COLD_START
    start = now_ms()
    status_code = 500
    response = None
    try:
        response = await call_next(request)
        status_code = getattr(response, "status_code", 200) or 200
        return response
    except HTTPException as exc:
        status_code = exc.status_code
        raise
    except Exception:
        status_code = 500
        raise
    finally:
        end = now_ms()
        is_cold_start = _COLD_START
        _COLD_START = False
        try:
            content_length = None
            if response is not None:
                raw = response.headers.get("content-length")
                if raw is not None:
                    try:
                        content_length = int(raw)
                    except ValueError:
                        content_length = None
            put_request_metrics(
                request=request,
                status_code=int(status_code),
                duration_ms=duration_ms(start, end),
                is_cold_start=is_cold_start,
                content_length_bytes=content_length,
            )
        except Exception:
            logger.exception("Failed to emit CloudWatch metrics")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    """Ensure all errors return JSON so API Gateway / clients never get plain-text 500."""
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )


# Lambda handler
handler = Mangum(app, lifespan="off")


# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Health check routes
@app.get("/")
def read_root():
    return {"message": "ImageCore is running"}


logger.info("ImageCore Backend started")