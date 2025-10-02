"""
Upload utility functions for Cloudflare R2 storage.
Pure utility functions without FastAPI dependencies.
"""
import logging
import os
from io import BytesIO
from typing import Optional, Union

import boto3
import requests
from botocore.client import Config

from utils.config import R2_CONFIG

logger = logging.getLogger(__name__)


class R2Uploader:
    """
    Cloudflare R2 storage uploader.
    Provides methods to upload files from various sources.
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize R2 uploader with configuration.

        Args:
            config: Optional custom R2 config, defaults to R2_CONFIG from config.py
        """
        self.config = config or R2_CONFIG
        self._s3_client = None

    @property
    def s3_client(self):
        """Lazy initialization of S3 client."""
        if self._s3_client is None:
            self._s3_client = boto3.client(
                "s3",
                region_name=self.config["region_name"],
                endpoint_url=self.config["endpoint_url"],
                aws_access_key_id=self.config["access_key_id"],
                aws_secret_access_key=self.config["secret_access_key"],
                config=Config(signature_version="s3v4"),
            )
        return self._s3_client

    def upload_buffer(
        self,
        buffer: Union[BytesIO, bytes],
        key: str,
        content_type: str = "image/jpeg",
    ) -> str:
        """
        Upload a buffer to R2 storage.

        Args:
            buffer: File buffer or bytes to upload
            key: Object key (path) in R2
            content_type: MIME type of the content

        Returns:
            Public CDN URL of the uploaded file

        Raises:
            Exception: If upload fails
        """
        try:
            # Ensure buffer is bytes-like
            if isinstance(buffer, BytesIO):
                buffer.seek(0)
                data = buffer.read()
            else:
                data = buffer

            # Upload to R2
            self.s3_client.put_object(
                Bucket=self.config["bucket_name"],
                Key=key,
                Body=data,
                ContentType=content_type,
            )

            # Return CDN URL
            cdn_url = f"{self.config['cdn_base_url']}/{key}"
            logger.info(f"Successfully uploaded to R2: {cdn_url}")
            return cdn_url

        except Exception as e:
            logger.error(f"Failed to upload to R2: {e}")
            raise

    def upload_from_url(
        self,
        image_url: str,
        key: str,
        content_type: Optional[str] = None,
        timeout: int = 30,
    ) -> Optional[str]:
        """
        Download an image from URL and upload to R2.

        Args:
            image_url: Source image URL
            key: Target key (path) in R2
            content_type: Optional content type, auto-detected if None
            timeout: Download timeout in seconds

        Returns:
            CDN URL if successful, None otherwise
        """
        try:
            # Download image
            response = requests.get(image_url, timeout=timeout)
            response.raise_for_status()

            # Auto-detect content type if not provided
            if content_type is None:
                content_type = response.headers.get("Content-Type", "image/jpeg")

            # Upload to R2
            buffer = BytesIO(response.content)
            return self.upload_buffer(buffer, key, content_type)

        except requests.RequestException as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to upload image from URL: {e}")
            return None

    def upload_file(
        self,
        file_path: str,
        key: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Upload a local file to R2.

        Args:
            file_path: Path to local file
            key: Optional target key, uses filename if not provided
            content_type: Optional content type, auto-detected if None

        Returns:
            CDN URL of uploaded file

        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If upload fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Use filename as key if not provided
        if key is None:
            filename = os.path.basename(file_path)
            key = f"{self.config['default_folder']}/{filename}"

        # Auto-detect content type from extension
        if content_type is None:
            ext = os.path.splitext(file_path)[1].lower()
            content_type_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
                ".svg": "image/svg+xml",
            }
            content_type = content_type_map.get(ext, "application/octet-stream")

        # Read and upload file
        with open(file_path, "rb") as f:
            return self.upload_buffer(f.read(), key, content_type)

    def generate_key(
        self,
        filename: str,
        folder: Optional[str] = None,
        add_timestamp: bool = False,
    ) -> str:
        """
        Generate a full object key for uploading.

        Args:
            filename: Base filename
            folder: Optional folder path, uses default if None
            add_timestamp: Whether to add timestamp suffix for uniqueness

        Returns:
            Full object key path
        """
        import time
        import uuid

        if folder is None:
            folder = self.config["default_folder"]

        # Ensure folder ends with /
        if folder and not folder.endswith("/"):
            folder = f"{folder}/"

        # Add uniqueness suffix if requested
        if add_timestamp:
            base, ext = os.path.splitext(filename)
            random_str = str(uuid.uuid4()).replace("-", "")[:8]
            filename = f"{base}_{int(time.time())}_{random_str}{ext}"

        return f"{folder}{filename}"


# Convenience functions for backward compatibility
def upload_to_r2(
    buffer: Union[BytesIO, bytes],
    key: str,
    content_type: str = "image/jpeg",
) -> str:
    """
    Upload buffer to R2 (backward compatible).

    Args:
        buffer: File buffer to upload
        key: Object key in R2
        content_type: MIME type

    Returns:
        CDN URL of uploaded file
    """
    uploader = R2Uploader()
    return uploader.upload_buffer(buffer, key, content_type)


def upload_by_url(
    src_image: str,
    path_without_ext: str,
    ext: str = "",
) -> Optional[str]:
    """
    Download and upload image from URL (backward compatible).

    Args:
        src_image: Source image URL
        path_without_ext: Target path without extension
        ext: Optional extension

    Returns:
        CDN URL if successful, None otherwise
    """
    uploader = R2Uploader()

    # Detect extension from URL if not provided
    if not ext:
        url_path = src_image.split("?")[0]
        ext = os.path.splitext(url_path)[1]

    # Build full key
    key = f"{path_without_ext}{ext}"

    return uploader.upload_from_url(src_image, key)
