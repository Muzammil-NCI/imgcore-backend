from fastapi import APIRouter, File, HTTPException, UploadFile

from app.constants.image_actions import ALLOWED_IMAGE_CONTENT_TYPES, MAX_IMAGE_SIZE_BYTES
from app.models import TransformRequestBody
from app.services import ImageProcessingService, UploadService

router = APIRouter()

image_processing_service = ImageProcessingService()
upload_service = UploadService()



@router.post("/upload")
async def upload_file(
    file: UploadFile = File(..., description="Image file to upload (max 2 MB, JPEG/PNG/GIF/WebP only)"),
):
    """Upload an image to S3 and return the object key. Max size 2 MB; only JPEG, PNG, GIF, WebP."""
    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is 2 MB",
        )
    content_type = (file.content_type or "").strip().lower()
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: JPEG, PNG, GIF, WebP. Got: {content_type or 'unknown'}.",
        )
    key = upload_service.upload_bytes_to_s3(content, content_type)
    return {"key": key}


@router.post("/transform")
async def transform_image(body: TransformRequestBody):
    """Transform an image from a URI. Request body: uri (string), action (string), parameters (optional object)."""
    params = body.parameters
    return await image_processing_service.transform_image(
        uri=body.uri,
        action=body.action,
        parameters=params,
    )
