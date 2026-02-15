import boto3
from app.core.config import settings

s3_client = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT_URL,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    use_ssl=False,
)

try:
    s3_client.head_bucket(Bucket=settings.S3_BUCKET)
    print(f"OK - Bucket '{settings.S3_BUCKET}' zaten mevcut")
except:
    s3_client.create_bucket(Bucket=settings.S3_BUCKET)
    print(f"OK - Bucket '{settings.S3_BUCKET}' olusturuldu")
