"""S3-compatible storage service (MinIO for local, S3 for production)."""
import aioboto3
from botocore.exceptions import ClientError
from app.core.config import settings


class StorageService:
    def __init__(self):
        self.session = aioboto3.Session()
        self.bucket = settings.S3_BUCKET_NAME
        self._client_kwargs = {
            "endpoint_url": settings.S3_ENDPOINT_URL,
            "aws_access_key_id": settings.S3_ACCESS_KEY,
            "aws_secret_access_key": settings.S3_SECRET_KEY,
            "region_name": settings.S3_REGION,
        }

    async def ensure_bucket(self):
        async with self.session.client("s3", **self._client_kwargs) as s3:
            try:
                await s3.head_bucket(Bucket=self.bucket)
            except ClientError:
                await s3.create_bucket(Bucket=self.bucket)

    async def upload_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream"):
        async with self.session.client("s3", **self._client_kwargs) as s3:
            await s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )

    async def download_bytes(self, key: str) -> bytes:
        async with self.session.client("s3", **self._client_kwargs) as s3:
            response = await s3.get_object(Bucket=self.bucket, Key=key)
            return await response["Body"].read()

    async def delete_object(self, key: str):
        async with self.session.client("s3", **self._client_kwargs) as s3:
            await s3.delete_object(Bucket=self.bucket, Key=key)

    async def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        async with self.session.client("s3", **self._client_kwargs) as s3:
            url = await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url

    async def object_exists(self, key: str) -> bool:
        async with self.session.client("s3", **self._client_kwargs) as s3:
            try:
                await s3.head_object(Bucket=self.bucket, Key=key)
                return True
            except ClientError:
                return False
