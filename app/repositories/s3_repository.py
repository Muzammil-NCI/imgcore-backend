import os
import uuid
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from fastapi import HTTPException

from app.config import settings



class S3Repository:
    def __init__(self):
        self._client = None
        self._session = None

    # def _get_session(self):
    #     if self._session is None:
    #         self._session = boto3.Session(
    #             region_name=settings.aws.region,
    #             aws_access_key_id=settings.aws.access_key,
    #             aws_secret_access_key=settings.aws.secret_access_key,
    #         )
    #     return self._session
    
    def _get_client(self):
        if self._client is None:
            try:
                is_local = not os.getenv("AWS_LAMBDA_FUNCTION_NAME")
                client_kwargs: dict = {
                    "region_name": settings.aws.region,
                    "config": Config(signature_version="s3v4"),
                }
                if is_local:
                    load_dotenv()
                    access_key = os.getenv("AWS_ACCESS_KEY_ID")
                    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
                    if access_key and secret_key:
                        client_kwargs["aws_access_key_id"] = access_key
                        client_kwargs["aws_secret_access_key"] = secret_key
                self._client = boto3.client("s3", **client_kwargs)
            except ImportError:
                raise HTTPException(
                    status_code=503,
                    detail="boto3 is required for S3 uploads. Install with: pip install boto3",
                )
        return self._client

    def upload_file(
        self,
        file_bytes: bytes,
        content_type: str,
        key: Optional[str] = None,
    ) -> str:
        bucket = settings.aws.s3_bucket
        if not key:
            ext = "bin"
            if content_type:
                ext = content_type.split("/")[-1].split("+")[0] or "bin"
            key = f"uploads/{datetime.utcnow().strftime('%Y/%m/%d')}/{uuid.uuid4().hex}.{ext}"
        client = self._get_client()
        # client = self._get_session().resource("s3")
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=file_bytes,
            ContentType=content_type or "application/octet-stream",
        )
        return key

    def put_processed_image(
        self,
        file_bytes: bytes,
        content_type: str = "image/png",
        key: Optional[str] = None,
    ) -> str:
        """Save bytes to S3 under the processed/ directory and return the object URL."""
        bucket = settings.aws.s3_bucket
        if not bucket:
            raise HTTPException(
                status_code=503,
                detail="S3 bucket is not configured. Set S3_BUCKET_NAME.",
            )
        if not key:
            ext = content_type.split("/")[-1].split("+")[0] if content_type else "png"
            key = f"processed/{datetime.utcnow().strftime('%Y/%m/%d')}/{uuid.uuid4().hex}.{ext}"
        else:
            key = key if key.startswith("processed/") else f"processed/{key}"
        client = self._get_client()
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=file_bytes,
            ContentType=content_type or "image/png",
        )
        url = f"https://{bucket}.s3.{settings.aws.region}.amazonaws.com/{key}"
        return url

    def generate_presigned_url(
        self,
        object_url_or_key: str,
        bucket: Optional[str] = None,
        expires_in: int = 3600,
    ) -> str:
        """Generate a presigned URL for GET. Accepts either an object URL or an object key."""
        bucket = bucket or settings.aws.s3_bucket
        if not bucket:
            raise HTTPException(
                status_code=503,
                detail="S3 bucket is not configured. Set S3_BUCKET_NAME.",
            )
        key: str
        if object_url_or_key.startswith("http://") or object_url_or_key.startswith("https://"):
            # Parse virtual-hosted-style URL: https://bucket.s3.region.amazonaws.com/key
            parsed = urlparse(object_url_or_key)
            path = parsed.path.lstrip("/")
            if ".s3." in parsed.netloc and "." in parsed.netloc:
                # bucket.s3.region.amazonaws.com -> first part is bucket
                bucket = parsed.netloc.split(".s3.")[0]
            key = path
        else:
            key = object_url_or_key.lstrip("/")
        client = self._get_client()
        try:
            return client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to generate presigned URL: {e!s}",
            )

    def get_object(self, key: str, bucket: Optional[str] = None) -> bytes:
        """Fetch an object from S3 and return its content as bytes."""
        bucket = bucket or settings.aws.s3_bucket
        if not bucket:
            raise HTTPException(
                status_code=503,
                detail="S3 bucket is not configured. Set S3_BUCKET_NAME.",
            )
        client = self._get_client()
        try:
            response = client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise HTTPException(
                    status_code=404,
                    detail=f"Object not found: s3://{bucket}/{key}",
                )
            raise HTTPException(
                status_code=422,
                detail=f"Failed to fetch image from S3: {e!s}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to fetch image from S3: {e!s}",
            )
