#!/usr/bin/env python3
"""
Upload local images to Cloudflare R2 storage.

Usage:
    # Upload single file
    python upload_images_to_r2.py path/to/image.jpg

    # Upload with custom R2 key
    python upload_images_to_r2.py path/to/image.jpg --key "custom/path/image.jpg"

    # Upload entire directory
    python upload_images_to_r2.py path/to/images/ --recursive

    # Upload with folder prefix
    python upload_images_to_r2.py path/to/images/ --folder "drama/episode1"

    # Dry run (show what would be uploaded)
    python upload_images_to_r2.py path/to/images/ --dry-run
"""

import sys
import os
from pathlib import Path
import argparse
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.upload import R2Uploader
from utils.config import R2_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_image_file(file_path: str) -> bool:
    """Check if file is an image based on extension."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}
    ext = os.path.splitext(file_path)[1].lower()
    return ext in image_extensions


def upload_single_file(uploader: R2Uploader, file_path: str, r2_key: str = None, dry_run: bool = False) -> bool:
    """
    Upload a single file to R2.

    Args:
        uploader: R2Uploader instance
        file_path: Path to local file
        r2_key: Optional custom R2 key, uses filename if not provided
        dry_run: If True, only show what would be uploaded

    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False

    if not is_image_file(file_path):
        logger.warning(f"Skipping non-image file: {file_path}")
        return False

    # Generate R2 key if not provided
    if r2_key is None:
        filename = os.path.basename(file_path)
        r2_key = filename

    file_size = os.path.getsize(file_path) / 1024  # KB

    if dry_run:
        logger.info(f"[DRY RUN] Would upload: {file_path} -> {r2_key} ({file_size:.1f} KB)")
        return True

    try:
        logger.info(f"Uploading: {file_path} -> {r2_key} ({file_size:.1f} KB)")
        cdn_url = uploader.upload_file(file_path, r2_key)
        logger.info(f"✅ Success! CDN URL: {cdn_url}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to upload {file_path}: {e}")
        return False


def upload_directory(uploader: R2Uploader, dir_path: str, folder: str = None,
                     recursive: bool = False, dry_run: bool = False):
    """
    Upload all images in a directory to R2.

    Args:
        uploader: R2Uploader instance
        dir_path: Path to directory
        folder: Optional folder prefix for R2 keys
        recursive: If True, upload subdirectories recursively
        dry_run: If True, only show what would be uploaded
    """
    if not os.path.isdir(dir_path):
        logger.error(f"Directory not found: {dir_path}")
        return

    dir_path = os.path.abspath(dir_path)
    success_count = 0
    fail_count = 0
    skip_count = 0

    # Get all files
    if recursive:
        files = []
        for root, _, filenames in os.walk(dir_path):
            for filename in filenames:
                files.append(os.path.join(root, filename))
    else:
        files = [os.path.join(dir_path, f) for f in os.listdir(dir_path)
                if os.path.isfile(os.path.join(dir_path, f))]

    # Filter image files
    image_files = [f for f in files if is_image_file(f)]

    if not image_files:
        logger.warning(f"No image files found in {dir_path}")
        return

    logger.info(f"Found {len(image_files)} image(s) to upload")
    logger.info("-" * 80)

    for file_path in image_files:
        # Generate R2 key
        if recursive:
            # Preserve directory structure relative to base dir
            rel_path = os.path.relpath(file_path, dir_path)
            if folder:
                r2_key = f"{folder}/{rel_path}"
            else:
                r2_key = rel_path
        else:
            filename = os.path.basename(file_path)
            if folder:
                r2_key = f"{folder}/{filename}"
            else:
                r2_key = filename

        # Normalize path separators for R2 (use forward slash)
        r2_key = r2_key.replace(os.sep, '/')

        if upload_single_file(uploader, file_path, r2_key, dry_run):
            success_count += 1
        else:
            fail_count += 1

    # Summary
    logger.info("-" * 80)
    if dry_run:
        logger.info(f"[DRY RUN] Would upload {success_count} file(s)")
    else:
        logger.info(f"Upload complete: {success_count} succeeded, {fail_count} failed")
        if success_count > 0:
            logger.info(f"CDN Base URL: {R2_CONFIG['cdn_base_url']}")


def main():
    parser = argparse.ArgumentParser(
        description='Upload local images to Cloudflare R2 storage',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        'path',
        help='Path to image file or directory'
    )

    parser.add_argument(
        '--key', '-k',
        help='Custom R2 key for single file upload (e.g., "drama/ep1/char.jpg")'
    )

    parser.add_argument(
        '--folder', '-f',
        help='Folder prefix for R2 keys (e.g., "drama/episode1")'
    )

    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Upload directory recursively (preserves subdirectory structure)'
    )

    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Show what would be uploaded without actually uploading'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize uploader
    uploader = R2Uploader()

    # Check if path exists
    if not os.path.exists(args.path):
        logger.error(f"Path not found: {args.path}")
        sys.exit(1)

    # Upload
    if os.path.isfile(args.path):
        # Single file upload
        if args.recursive:
            logger.warning("--recursive flag is ignored for single file upload")

        success = upload_single_file(uploader, args.path, args.key, args.dry_run)
        sys.exit(0 if success else 1)

    elif os.path.isdir(args.path):
        # Directory upload
        if args.key:
            logger.warning("--key flag is ignored for directory upload, use --folder instead")

        upload_directory(uploader, args.path, args.folder, args.recursive, args.dry_run)
        sys.exit(0)

    else:
        logger.error(f"Invalid path: {args.path}")
        sys.exit(1)


if __name__ == '__main__':
    main()
