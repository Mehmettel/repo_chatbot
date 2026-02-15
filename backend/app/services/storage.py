"""
S3 uyumlu object storage adaptörü - BLUEPRINT: AWS S3 veya MinIO.
ADR-007: Konfigürasyon ile S3/MinIO seçimi.
"""
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.config import Config

from app.core.config import settings


def get_s3_client():
    """S3 uyumlu client (MinIO veya AWS)."""
    kwargs = {
        "aws_access_key_id": settings.S3_ACCESS_KEY,
        "aws_secret_access_key": settings.S3_SECRET_KEY,
        "region_name": settings.S3_REGION,
        "config": Config(signature_version="s3v4"),
    }
    if settings.S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
    return boto3.client("s3", **kwargs)


def upload_file(
    local_path: Path,
    s3_key: str,
    bucket: str | None = None,
    content_type: str = "video/mp4",
) -> str:
    """Dosyayı S3'e yükler; s3_key döner."""
    bkt = bucket or settings.S3_BUCKET
    client = get_s3_client()
    client.upload_file(
        str(local_path),
        bkt,
        s3_key,
        ExtraArgs={"ContentType": content_type},
    )
    return s3_key


def upload_fileobj(
    file_obj: BinaryIO,
    s3_key: str,
    bucket: str | None = None,
    content_type: str = "video/mp4",
) -> str:
    """Stream ile yükleme."""
    bkt = bucket or settings.S3_BUCKET
    client = get_s3_client()
    client.upload_fileobj(
        file_obj,
        bkt,
        s3_key,
        ExtraArgs={"ContentType": content_type},
    )
    return s3_key


def get_presigned_url(s3_key: str, bucket: str | None = None, expires_in: int = 3600) -> str:
    """Video izleme için geçici URL."""
    bkt = bucket or settings.S3_BUCKET
    client = get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bkt, "Key": s3_key},
        ExpiresIn=expires_in,
    )


def delete_file(s3_key: str, bucket: str | None = None) -> bool:
    """S3'den dosya siler."""
    bkt = bucket or settings.S3_BUCKET
    client = get_s3_client()
    try:
        client.delete_object(Bucket=bkt, Key=s3_key)
        return True
    except Exception as e:
        print(f"S3 delete error: {e}")
        return False


def delete_files(s3_keys: list[str], bucket: str | None = None) -> bool:
    """S3'den birden fazla dosya siler."""
    if not s3_keys:
        return True
    bkt = bucket or settings.S3_BUCKET
    client = get_s3_client()
    try:
        client.delete_objects(
            Bucket=bkt,
            Delete={"Objects": [{"Key": key} for key in s3_keys]}
        )
        return True
    except Exception as e:
        print(f"S3 bulk delete error: {e}")
        return False


def ensure_bucket_exists(bucket: str | None = None) -> bool:
    """Bucket yoksa oluşturur. MinIO ilk çalıştırmada bucket yoktur."""
    bkt = bucket or settings.S3_BUCKET
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=bkt)
        return True
    except Exception:
        # Bucket yok, oluştur
        try:
            client.create_bucket(Bucket=bkt)
            print(f"[Storage] Bucket oluşturuldu: {bkt}")
            return True
        except Exception as e:
            print(f"[Storage] Bucket oluşturulamadı: {e}")
            return False
