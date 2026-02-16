import os
import logging
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Load .env file first (for local development)
load_dotenv()

class AWSSettings(BaseModel):
    region: str = "us-east-1"
    s3_bucket: str = ""
    uploads_folder: str = "uploads"
    
    @classmethod
    def from_env(cls):
        return cls(
            region=os.getenv("AWS_REGION", "us-east-1"),
            s3_bucket=os.getenv("S3_BUCKET_NAME", ""),
            uploads_folder=os.getenv("BUCKET_UPLOADS_FOLDER", "uploads"),
        )

class Settings(BaseSettings):
    aws: AWSSettings = AWSSettings.from_env()
    # def reload_from_env(self):
    #     self.aws = AWSSettings.from_env()
        
    #     print(f"Settings reloaded from environment variables - region: {self.aws.region}")

settings = Settings()
