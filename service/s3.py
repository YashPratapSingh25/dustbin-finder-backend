from io import BytesIO
from core.config import settings


class S3Service:
    def __init__(self, s3_client):
        self.s3 = s3_client

    async def get_presigned_url(self, object_name, expiration : int = settings.PRESIGNED_URL_DURATION) -> str:
        url = await self.s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": object_name,
                "ResponseContentDisposition": "inline",  # Tells the browser to open the file in browser
            },
            ExpiresIn=expiration,
        )

        return url

    async def upload_file(
        self,
        file_bytes: bytes,
        object_name: str,
    ) -> str:
        await self.s3.upload_fileobj(
            BytesIO(file_bytes), settings.S3_BUCKET_NAME, object_name
        )

        url = await self.get_presigned_url(object_name)

        return url