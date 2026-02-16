from fastapi import UploadFile

from app.repositories import S3Repository


class UploadService:
    def __init__(self):
        self.s3_repository = S3Repository()

    async def upload_to_s3(self, file: UploadFile) -> str:
        content = await file.read()
        content_type = file.content_type or "application/octet-stream"
        return self.s3_repository.upload_file(
            file_bytes=content,
            content_type=content_type,
        )

    def upload_bytes_to_s3(self, content: bytes, content_type: str) -> str:
        """Upload pre-read bytes to S3 (e.g. after validation)."""
        return self.s3_repository.upload_file(
            file_bytes=content,
            content_type=content_type,
        )
