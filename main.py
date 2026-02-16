import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from app import router

logger = logging.getLogger(__name__)

app = FastAPI(title="ImageCore API", description="API for image transformation and processing")


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