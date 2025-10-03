"""
File upload endpoints.
Handles image uploads via file, Base64, or URL.
"""
import base64
import logging
import os
import time
import uuid
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, Request, Response, UploadFile

from utils.upload import R2Uploader
from api.middleware.auth import require_auth, UserPrincipal
from api.schemas import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])


@router.api_route("/upload-image", methods=["GET", "POST", "OPTIONS"])
async def upload_image(
    req: Request,
    response: Response,
    type: Optional[str] = Query("file", description="Upload type: file, base64, or url"),
    folder: Optional[str] = Query("", description="Optional folder path in R2"),
    filename: Optional[str] = Query(None, description="Custom filename (optional)"),
    file: Optional[UploadFile] = File(None, description="File for type=file"),
    user: UserPrincipal = Depends(require_auth),
):
    """
    Handle image uploads via file, Base64, or remote URL input.

    Upload types:
    - file: Upload from multipart file
    - base64: Upload from base64-encoded data in JSON body
    - url: Download from URL and upload

    Returns:
        JSON response with upload status and CDN URL
    """
    try:
        # Initialize uploader
        uploader = R2Uploader()

        # Ensure folder format
        if folder and not folder.endswith("/"):
            folder = f"{folder}/"

        # Variables to collect
        buffer = None
        content_type = None
        determined_filename = None

        # === Handle different upload types ===
        if type == "file":
            # Upload from multipart file
            if not file:
                response.status_code = 400
                return ApiResponse.error(code=400, message="No file provided (type=file)")

            determined_filename = filename or file.filename
            content_type = file.content_type or "image/jpeg"
            file_content = await file.read()
            buffer = BytesIO(file_content)

        elif type == "base64":
            # Upload from base64 data
            req_body = await req.json()
            base64_data = req_body.get("base64_data")
            if not base64_data:
                response.status_code = 400
                return ApiResponse.error(code=400, message="No base64_data provided (type=base64)")

            # Parse data URL format: data:image/jpeg;base64,<data>
            if "," in base64_data:
                header, base64_data = base64_data.split(",", 1)
                content_type = header.split(":")[1].split(";")[0] if ":" in header else "image/jpeg"
            else:
                content_type = req_body.get("content_type", "image/jpeg")

            # Decode base64
            try:
                file_content = base64.b64decode(base64_data)
                buffer = BytesIO(file_content)
            except Exception as e:
                response.status_code = 400
                return ApiResponse.error(code=400, message=f"Base64 decode failed: {str(e)}")

            # Determine filename
            ext = req_body.get("ext", ".jpg")
            if not ext.startswith("."):
                ext = f".{ext}"
            determined_filename = filename or req_body.get("filename") or f"image_{int(time.time())}{ext}"

        elif type == "url":
            # Download from URL and upload
            req_body = await req.json()
            image_url = req_body.get("url")
            if not image_url:
                response.status_code = 400
                return ApiResponse.error(code=400, message="No url provided (type=url)")

            # Let uploader handle download
            try:
                # Detect extension from URL
                url_path = image_url.split("?")[0]
                ext = os.path.splitext(url_path)[1] or ".jpg"

                # Determine filename
                determined_filename = filename or req_body.get("filename") or f"image_{int(time.time())}{ext}"

                # Generate key
                if not filename:
                    # Add uniqueness for auto-generated names
                    base_name, file_ext = os.path.splitext(determined_filename)
                    random_str = str(uuid.uuid4()).replace("-", "")[:8]
                    determined_filename = f"{base_name}_{random_str}{file_ext}"

                object_key = uploader.generate_key(determined_filename, folder=folder)

                # Upload from URL directly
                cdn_url = uploader.upload_from_url(image_url, object_key)

                if not cdn_url:
                    response.status_code = 500
                    return ApiResponse.error(code=500, message="Failed to download or upload image")

                return ApiResponse.success(
                    data={
                        "url": cdn_url,
                        "filename": determined_filename,
                        "content_type": "image/jpeg",
                    },
                    message="Image uploaded successfully"
                )

            except Exception as e:
                response.status_code = 500
                return ApiResponse.error(code=500, message=f"Failed to process URL upload: {str(e)}")

        else:
            response.status_code = 400
            return ApiResponse.error(code=400, message=f"Unsupported upload type: {type}")

        # === For file and base64 types, upload buffer ===
        if buffer is None:
            response.status_code = 500
            return ApiResponse.error(code=500, message="Internal error: no buffer created")

        # Add uniqueness suffix if no custom filename
        if not filename:
            base_name, ext = os.path.splitext(determined_filename)
            if not ext:
                ext = ".jpg" if content_type == "image/jpeg" else f".{content_type.split('/')[-1]}"
            random_str = str(uuid.uuid4()).replace("-", "")[:8]
            determined_filename = f"{base_name}_{random_str}{ext}"

        # Generate full object key
        object_key = uploader.generate_key(determined_filename, folder=folder)

        # Upload to R2
        try:
            cdn_url = uploader.upload_buffer(buffer, object_key, content_type)

            return ApiResponse.success(
                data={
                    "url": cdn_url,
                    "filename": determined_filename,
                    "content_type": content_type,
                    "size": len(buffer.getvalue()),
                },
                message="Image uploaded successfully"
            )

        except Exception as e:
            logger.error(f"Upload to R2 failed: {str(e)}")
            response.status_code = 500
            return ApiResponse.error(code=500, message=f"Upload failed: {str(e)}")

    except Exception as e:
        logger.error(f"Error handling upload request: {str(e)}")
        response.status_code = 500
        return ApiResponse.error(code=500, message=f"Server error: {str(e)}")
