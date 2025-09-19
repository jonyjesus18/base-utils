from typing import Iterator
from dotenv import load_dotenv
from contextlib import contextmanager
from loguru import logger
import os
import boto3
from botocore.exceptions import ClientError
import tempfile
import os
from pathlib import Path

load_dotenv()


class S3Manager:
    """
    A manager class for interacting with an S3-compatible storage service
    (e.g., Wasabi, AWS S3).

    Provides utility methods for uploading and downloading files.
    """

    def __init__(self, region: str = "eu-west-1") -> None:
        """
        Initialize the S3Manager.

        Args:
            region (str): Cloud storage region (default: 'eu-west-1').
        """
        aws_access_key: str | None = os.getenv("AWS_ACCESS_KEY")
        aws_secret_key: str | None = os.getenv("AWS_ACCESS_SECRET_KEY")

        if not aws_access_key or not aws_secret_key:
            raise ValueError(
                "AWS_ACCESS_KEY or AWS_ACCESS_SECRET_KEY not set in environment"
            )

        self.region = region
        self.s3 = boto3.client(
            "s3",
            endpoint_url=f"https://s3.{region}.wasabisys.com",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
        )
        logger.debug(f"S3Manager initialized for region={region}")

    def upload_file(
        self,
        bucket: str,
        source_file_path: str,
        dest_file_path: str,
    ) -> bool:
        """
        Upload a file to the specified S3 bucket.

        Args:
            bucket (str): The name of the target S3 bucket.
            source_file_path (str): Local path to the file to upload.
            dest_file_path (str): Destination path in the S3 bucket.

        Returns:
            bool: True if upload succeeded, False otherwise.
        """
        logger.info(f"Uploading {source_file_path} → s3://{bucket}/{dest_file_path}")
        try:
            self.s3.upload_file(source_file_path, bucket, dest_file_path)
            logger.success("Upload completed successfully.")
            return True
        except ClientError as e:
            logger.error(f"Upload failed: {e}")
            return False

    def download_file(
        self,
        bucket: str,
        source_file_path: str,
        dest_file_path: str,
    ) -> bool:
        """
        Download a file from the specified S3 bucket.

        Args:
            bucket (str): The name of the S3 bucket.
            source_file_path (str): Path of the file in the S3 bucket.
            dest_file_path (str): Local destination path for the downloaded file.

        Returns:
            bool: True if download succeeded, False otherwise.
        """
        logger.info(f"Downloading s3://{bucket}/{source_file_path} → {dest_file_path}")
        try:
            self.s3.download_file(bucket, source_file_path, dest_file_path)
            logger.success("Download completed successfully.")
            return True
        except ClientError as e:
            logger.error(f"Download failed: {e}")
            return False

    @contextmanager
    def download_file_temp(
        self,
        bucket: str,
        source_file_path: str,
    ) -> Iterator[str]:
        """
        Context manager to download S3 file to temp location with auto-cleanup.

        Usage:
            with s3.download_file_temp(bucket, source) as temp_path:
                process_file(temp_path)
            # File is automatically deleted after context
        """
        temp_path = None
        try:
            # Create and get temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_path = temp_file.name
            temp_file.close()

            # Download file
            logger.info(f"Downloading s3://{bucket}/{source_file_path} → {temp_path}")
            self.s3.download_file(bucket, source_file_path, temp_path)
            logger.success("Download completed successfully")

            yield temp_path

        except ClientError as e:
            logger.error(f"Download failed: {e}")
            raise

        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
                logger.debug(f"Cleaned up temporary file: {temp_path}")