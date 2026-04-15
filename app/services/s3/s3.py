"""
S3 service for handling file uploads to AWS S3 and S3-compatible storage.
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.client import Config
from dotenv import load_dotenv
import asyncio
import concurrent.futures
import mimetypes
from urllib.parse import urlparse
from app.utils.logging import get_logger
from app.utils.validation import validate_url, validate_file_extension

# Load environment variables from .env file if it exists
load_dotenv()

# Configure enhanced logging
logger = get_logger(module="s3_service", component="storage")


class S3Service:
    """S3 service for handling file uploads to AWS S3 and S3-compatible storage."""

    def __init__(self):
        """Initialize S3 service."""
        # Get S3 credentials from environment variables (support both AWS and S3-compatible)
        self.access_key = os.environ.get("S3_ACCESS_KEY") or os.environ.get(
            "AWS_ACCESS_KEY_ID"
        )
        self.secret_key = os.environ.get("S3_SECRET_KEY") or os.environ.get(
            "AWS_SECRET_ACCESS_KEY"
        )
        self.bucket_name = os.environ.get("S3_BUCKET_NAME") or os.environ.get(
            "AWS_BUCKET_NAME"
        )
        self.region = os.environ.get("S3_REGION") or os.environ.get("AWS_REGION")
        self.endpoint_url = os.environ.get("S3_ENDPOINT_URL")

        # Auto-detect Digital Ocean Spaces configuration
        if (
            self.endpoint_url
            and "digitalocean" in self.endpoint_url.lower()
            and (not self.bucket_name or not self.region)
        ):
            logger.info(
                "Digital Ocean endpoint detected with missing bucket or region. Extracting from URL."
            )
            try:
                # Extract bucket name and region from URL like https://sgp-labs.nyc3.digitaloceanspaces.com
                parsed_url = urlparse(self.endpoint_url)
                if parsed_url.hostname:
                    hostname_parts = parsed_url.hostname.split(".")

                    # The first part is the bucket name (sgp-labs)
                    if not self.bucket_name and len(hostname_parts) > 0:
                        self.bucket_name = hostname_parts[0]
                        logger.info(
                            f"Extracted bucket name from URL: {self.bucket_name}"
                        )

                    # The second part is the region (nyc3)
                    if not self.region and len(hostname_parts) > 1:
                        self.region = hostname_parts[1]
                        logger.info(f"Extracted region from URL: {self.region}")

            except Exception as e:
                logger.warning(
                    f"Failed to parse Digital Ocean URL: {e}. Using provided values."
                )

        # Thread pool for handling blocking S3 operations
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

        # Print environment variables for debugging (without sensitive info)
        logger.debug(f"S3_ACCESS_KEY: {'*' * 8 if self.access_key else 'Not Set'}")
        logger.debug(f"S3_SECRET_KEY: {'*' * 8 if self.secret_key else 'Not Set'}")
        logger.debug(f"S3_BUCKET_NAME: {self.bucket_name}")
        logger.debug(f"S3_REGION: {self.region}")
        logger.debug(f"S3_ENDPOINT_URL: {self.endpoint_url}")

        # Check if credentials are provided
        using_dummy_credentials = (
            self.access_key == "dummy_access_key_id"
            or self.secret_key == "dummy_secret_access_key"
            or self.bucket_name == "dummy-bucket-name"
        )

        if using_dummy_credentials:
            logger.warning(
                "Using dummy S3 credentials. S3 uploads will return mock URLs instead."
            )
            self.s3_client = None
            return

        # Initialize S3 client
        try:
            # Make sure all required values are strings
            self.access_key = str(self.access_key)
            self.secret_key = str(self.secret_key)
            self.bucket_name = str(self.bucket_name)
            self.region = str(self.region)

            # Build S3 client config
            s3_config = {
                "aws_access_key_id": self.access_key,
                "aws_secret_access_key": self.secret_key,
                "region_name": self.region,
            }

            # Add endpoint URL for S3-compatible services
            if self.endpoint_url:
                s3_config["endpoint_url"] = self.endpoint_url
                logger.info(f"Using S3-compatible endpoint: {self.endpoint_url}")

                # Check if this is a MinIO server
                is_minio = (
                    "minio" in self.endpoint_url.lower()
                    or "localhost" in self.endpoint_url.lower()
                    or "127.0.0.1" in self.endpoint_url
                )

                # Configure addressing style
                if is_minio:
                    s3_config["config"] = Config(
                        s3={"addressing_style": "path"}, signature_version="s3v4"
                    )
                    # Only disable SSL verification for local dev MinIO, not production
                    is_local = "localhost" in self.endpoint_url.lower() or "127.0.0.1" in self.endpoint_url
                    if is_local:
                        s3_config["verify"] = False
                    logger.info(
                        f"Detected MinIO server, using path-style addressing for {self.endpoint_url}"
                    )

            self.s3_client = boto3.client("s3", **s3_config)
            logger.info(
                f"S3 client initialized with region {self.region} and bucket {self.bucket_name}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
            return

        # For MinIO, set bucket policy to allow public read access
        # MinIO doesn't respect ACL headers the same way AWS S3 does
        if self.endpoint_url and "minio" in self.endpoint_url.lower():
            self._ensure_minio_public_policy()

    def _ensure_minio_public_policy(self):
        """
        Set bucket policy for MinIO to allow public read access.

        MinIO doesn't respect ACL headers in the same way as AWS S3.
        Instead, we need to set a bucket policy to allow public reads.
        """
        try:
            # Define a policy that allows public read access to all objects in the bucket
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{self.bucket_name}/*"
                    }
                ]
            }

            import json

            policy_json = json.dumps(bucket_policy)

            # Try to set the bucket policy
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=policy_json
            )

            logger.info(f"Successfully set public read policy for MinIO bucket: {self.bucket_name}")

        except ClientError as e:
            # If the policy already exists or there's a permission issue, log but don't fail
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "InvalidAccessKeyId":
                logger.warning(f"Cannot set bucket policy due to permissions: {e}")
            else:
                logger.warning(f"Could not set bucket policy (may already exist): {e}")
        except Exception as e:
            logger.warning(f"Failed to set bucket policy for MinIO: {e}")

    def _upload_file_sync(
        self,
        file_path: str,
        object_name: str | None = None,
        content_type: str | None = None,
        public: bool = True,
    ) -> dict:
        """
        Synchronous version of upload_file to be run in thread pool.

        Args:
            file_path: Path to the file to upload
            object_name: S3 object name. If not specified, file_path's basename will be used
            content_type: MIME type of the file. If not specified, will be auto-detected

        Returns:
            Dictionary containing upload metadata: URL, MIME type, extension, and file size
        """
        # Get file metadata
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        # Extract extension from object_name (user's filename), not temp file_path
        file_extension = ""
        if object_name:
            file_extension = os.path.splitext(object_name)[1].lower().lstrip(".")

        # If no extension in object_name, try to get it from original file_path
        if not file_extension:
            file_extension = os.path.splitext(file_path)[1].lower().lstrip(".")

        # If we have dummy credentials, return a mock response
        if self.s3_client is None:
            # Check if using dummy credentials explicitly
            using_dummy = (
                self.access_key == "dummy_access_key_id"
                or self.secret_key == "dummy_secret_access_key"
                or self.bucket_name == "dummy-bucket-name"
            )

            if using_dummy:
                logger.warning(
                    "S3 client not initialized. Returning a mock URL instead of uploading to S3."
                )
                mock_object_name = object_name or os.path.basename(file_path)
                return {
                    "file_url": f"https://example.com/mock-s3/{mock_object_name}",
                    "file_name": mock_object_name,
                    "file_extension": file_extension,
                    "mime_type": content_type or "application/octet-stream",
                    "file_size": file_size,
                }
            else:
                logger.error(
                    "S3 client not initialized and not using dummy credentials. Upload failed."
                )
                raise Exception("S3 client not initialized - check configuration")

        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} does not exist. Cannot upload to S3.")
            raise FileNotFoundError(f"File {file_path} does not exist")

        # If object_name is not specified, use file_path's basename
        if object_name is None:
            object_name = os.path.basename(file_path)

        # Auto-detect content type if not provided
        if content_type is None:
            # First try to guess from the object_name (preferred) if available
            if object_name:
                content_type, _ = mimetypes.guess_type(object_name)
                if content_type:
                    logger.info(
                        f"Detected Content-Type: {content_type} from object name: {object_name}"
                    )

            # Fallback to temp file path
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)

            if content_type is None:
                content_type = "application/octet-stream"

            # Manual mapping for common formats if mimetypes failed
            # Prioritize object_name extension over temp file extension
            target_file_extension = None
            if object_name:
                target_file_extension = os.path.splitext(object_name)[1].lower()
            if not target_file_extension:
                target_file_extension = os.path.splitext(file_path)[1].lower()

            if content_type == "application/octet-stream" or not content_type:
                manual_mapping = {
                    # Images
                    ".webp": "image/webp",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                    ".bmp": "image/bmp",
                    ".tiff": "image/tiff",
                    ".tif": "image/tiff",
                    ".svg": "image/svg+xml",
                    ".ico": "image/x-icon",
                    # Videos
                    ".mp4": "video/mp4",
                    ".avi": "video/x-msvideo",
                    ".mov": "video/quicktime",
                    ".wmv": "video/x-ms-wmv",
                    ".flv": "video/x-flv",
                    ".webm": "video/webm",
                    ".mkv": "video/x-matroska",
                    ".m4v": "video/x-m4v",
                    # Audio
                    ".mp3": "audio/mpeg",
                    ".wav": "audio/wav",
                    ".ogg": "audio/ogg",
                    ".flac": "audio/flac",
                    ".aac": "audio/aac",
                    ".m4a": "audio/mp4",
                    ".wma": "audio/x-ms-wma",
                    # Documents
                    ".pdf": "application/pdf",
                    ".doc": "application/msword",
                    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    ".xls": "application/vnd.ms-excel",
                    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    ".ppt": "application/vnd.ms-powerpoint",
                    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    ".txt": "text/plain",
                    ".csv": "text/csv",
                    ".json": "application/json",
                    ".xml": "application/xml",
                    ".html": "text/html",
                    ".css": "text/css",
                    ".js": "application/javascript",
                    # Archives
                    ".zip": "application/zip",
                    ".rar": "application/vnd.rar",
                    ".7z": "application/x-7z-compressed",
                    ".tar": "application/x-tar",
                    ".gz": "application/gzip",
                }
                if target_file_extension in manual_mapping:
                    content_type = manual_mapping[target_file_extension]
                    logger.info(
                        f"Detected Content-Type: {content_type} based on target file extension {target_file_extension}"
                    )
                else:
                    content_type = "application/octet-stream"

        # If user didn't provide an extension, auto-add one based on content type
        if not file_extension and content_type != "application/octet-stream":
            extension_mapping = {
                "image/jpeg": "jpg",
                "image/png": "png",
                "image/gif": "gif",
                "image/webp": "webp",
                "image/bmp": "bmp",
                "image/tiff": "tiff",
                "image/svg+xml": "svg",
                "video/mp4": "mp4",
                "video/webm": "webm",
                "video/quicktime": "mov",
                "audio/mpeg": "mp3",
                "audio/wav": "wav",
                "audio/ogg": "ogg",
                "application/pdf": "pdf",
                "text/plain": "txt",
                "application/json": "json",
            }

            if content_type in extension_mapping:
                file_extension = extension_mapping[content_type]
                object_name = f"{object_name}.{file_extension}"
                logger.info(
                    f"Auto-added extension: {object_name} (based on content type: {content_type})"
                )

        logger.info(f"Detected Content-Type: {content_type}")

        try:
            # Upload file to S3 with content type and ACL
            acl = "public-read" if public else "private"
            logger.info(
                f"Uploading file {file_path} to S3 bucket {self.bucket_name} as {object_name} (ACL: {acl})"
            )
            extra_args = {"ContentType": content_type, "ACL": acl}
            self.s3_client.upload_file(
                file_path, self.bucket_name, object_name, ExtraArgs=extra_args
            )

            # Generate the URL of the uploaded file
            if self.endpoint_url:
                # For S3-compatible services (like Digital Ocean Spaces or MinIO)

                # Parse the endpoint URL to get the scheme (http/https)
                parsed_endpoint = urlparse(self.endpoint_url)
                scheme = parsed_endpoint.scheme or "https"
                hostname = parsed_endpoint.hostname or ""
                port_part = f":{parsed_endpoint.port}" if parsed_endpoint.port else ""

                # Check for MinIO or explicit path-style addressing preference
                is_minio = (
                    "minio" in self.endpoint_url.lower()
                    or "localhost" in self.endpoint_url.lower()
                    or "127.0.0.1" in self.endpoint_url
                )

                if is_minio:
                    # Use path-style addressing: http://endpoint/bucket/key
                    base_url = f"{scheme}://{hostname}{port_part}"
                    url = f"{base_url}/{self.bucket_name}/{object_name}"
                else:
                    # Use virtual-hosted style: https://bucket.endpoint/key
                    # This logic handles DigitalOcean Spaces etc.

                    # Check if bucket name is already in the hostname
                    if self.bucket_name and not hostname.startswith(self.bucket_name):
                        # Bucket not in hostname - need to insert it
                        # Extract everything after the protocol
                        path_without_protocol = self.endpoint_url.replace(
                            f"{scheme}://", ""
                        )
                        url = f"{scheme}://{self.bucket_name}.{path_without_protocol.rstrip('/')}/{object_name}"
                    else:
                        # Bucket is already in the URL or no endpoint specified
                        url = f"{self.endpoint_url.rstrip('/')}/{object_name}"
            else:
                # For AWS S3, use the standard format (no URL encoding needed - filenames are pre-sanitized)
                url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{object_name}"

            logger.info(f"File uploaded successfully. URL: {url}")
            return {
                "file_url": url,
                "file_name": object_name,
                "file_extension": file_extension,
                "mime_type": content_type,
                "file_size": file_size,
            }
        except FileNotFoundError as e:
            logger.error(f"File not found: {file_path}. Error: {e}")
            raise
        except NoCredentialsError:
            logger.error("S3 credentials not found or invalid")
            raise
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {e}")
            raise

    async def upload_file(
        self,
        file_path: str,
        object_name: str | None = None,
        content_type: str | None = None,
        public: bool = True,
    ) -> str:
        """
        Upload a file to S3 bucket (async version that uses thread pool).

        Args:
            file_path: Path to the file to upload
            object_name: S3 object name. If not specified, file_path's basename will be used
            content_type: MIME type of the file. If not specified, will be auto-detected
            public: Whether the file should be publicly accessible (default: True)

        Returns:
            URL of the uploaded file
        """
        result = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            lambda: self._upload_file_sync(
                file_path, object_name, content_type, public
            ),
        )
        return result["file_url"]

    async def upload_file_with_metadata(
        self,
        file_path: str,
        object_name: str | None = None,
        content_type: str | None = None,
        public: bool = True,
    ) -> dict:
        """
        Upload a file to S3 bucket and return detailed metadata (async version that uses thread pool).

        Args:
            file_path: Path to the file to upload
            object_name: S3 object name. If not specified, file_path's basename will be used
            content_type: MIME type of the file. If not specified, will be auto-detected
            public: Whether the file should be publicly accessible (default: True)

        Returns:
            Dictionary containing upload metadata: URL, MIME type, extension, and file size
        """
        return await asyncio.get_event_loop().run_in_executor(
            self.executor,
            lambda: self._upload_file_sync(
                file_path, object_name, content_type, public
            ),
        )

    def _download_file_sync(
        self,
        object_name: str,
        download_path: str | None = None,
        bucket_name: str | None = None,
    ) -> str:
        """
        Synchronous version of download_file to be run in thread pool.

        Args:
            object_name: S3 object name to download
            download_path: Path to save the downloaded file. If not specified, a temporary file will be created.
            bucket_name: Optional bucket name to use instead of the default one

        Returns:
            Path to the downloaded file
        """
        # If we have dummy credentials, create a mock file instead
        if self.s3_client is None:
            logger.warning(
                "S3 client not initialized. Creating a mock file instead of downloading from S3."
            )

            # Create a mock file
            import tempfile

            if not download_path:
                # Create a temporary file with the same extension as the object_name
                _, ext = os.path.splitext(object_name)
                temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
                download_path = temp_file.name
                temp_file.close()

            # Write some dummy content to the file
            with open(download_path, "w") as f:
                f.write(f"This is a mock file for {object_name}")

            logger.info(f"Created mock file at {download_path}")
            return download_path

        # Create download path if not specified
        if not download_path:
            import tempfile

            # Create a temporary file with the same extension as the object_name
            _, ext = os.path.splitext(object_name)
            temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
            download_path = temp_file.name
            temp_file.close()

        try:
            # Use the provided bucket name or fall back to the default one
            target_bucket = bucket_name or self.bucket_name
            # Download file from S3
            logger.info(
                f"Downloading file {object_name} from S3 bucket {target_bucket} to {download_path}"
            )
            self.s3_client.download_file(target_bucket, object_name, download_path)
            logger.info(f"File downloaded successfully to {download_path}")
            return download_path
        except ClientError as e:
            logger.error(f"Error downloading file from S3: {e}")
            # Clean up the file if it exists
            if os.path.exists(download_path):
                os.unlink(download_path)
            raise
        except Exception as e:
            logger.error(f"Unexpected error during S3 download: {e}")
            # Clean up the file if it exists
            if os.path.exists(download_path):
                os.unlink(download_path)
            raise

    async def download_file(
        self,
        object_name: str,
        download_path: str | None = None,
        bucket_name: str | None = None,
    ) -> str:
        """
        Download a file from S3 bucket (async version that uses thread pool).

        Args:
            object_name: S3 object name to download
            download_path: Path to save the downloaded file. If not specified, a temporary file will be created.
            bucket_name: Optional bucket name to use instead of the default one

        Returns:
            Path to the downloaded file
        """
        return await asyncio.get_event_loop().run_in_executor(
            self.executor,
            lambda: self._download_file_sync(object_name, download_path, bucket_name),
        )

    def _delete_file_sync(self, object_name: str) -> bool:
        """
        Synchronous version of delete_file to be run in thread pool.

        Args:
            object_name: S3 object name to delete

        Returns:
            True if successful, False otherwise
        """
        # If we have dummy credentials, just return True
        if self.s3_client is None:
            logger.warning("S3 client not initialized. Skipping S3 delete operation.")
            return True

        try:
            # Delete file from S3
            logger.info(
                f"Deleting file {object_name} from S3 bucket {self.bucket_name}"
            )
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            logger.info(f"File {object_name} deleted successfully")
            return True
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during S3 delete: {e}")
            return False

    async def delete_file(self, object_name: str) -> bool:
        """
        Delete a file from S3 bucket (async version that uses thread pool).

        Args:
            object_name: S3 object name to delete

        Returns:
            True if successful, False otherwise
        """
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, lambda: self._delete_file_sync(object_name)
        )

    def _check_file_exists_sync(
        self, object_name: str, bucket_name: str | None = None
    ) -> bool:
        """
        Synchronous version of check_file_exists to be run in thread pool.

        Args:
            object_name: S3 object name to check
            bucket_name: Optional bucket name to use instead of the default one

        Returns:
            True if file exists, False otherwise
        """
        if self.s3_client is None:
            return False

        try:
            target_bucket = bucket_name or self.bucket_name
            self.s3_client.head_object(Bucket=target_bucket, Key=object_name)
            return True
        except ClientError:
            # If 404 or other client error, assume file doesn't exist
            return False
        except Exception as e:
            logger.error(f"Error checking file existence for {object_name}: {e}")
            return False

    async def check_file_exists(
        self, object_name: str, bucket_name: str | None = None
    ) -> bool:
        """
        Check if a file exists in S3 (async version that uses thread pool).

        Args:
            object_name: S3 object name to check
            bucket_name: Optional bucket name

        Returns:
            True if file exists, False otherwise
        """
        return await asyncio.get_event_loop().run_in_executor(
            self.executor,
            lambda: self._check_file_exists_sync(object_name, bucket_name),
        )

    def _generate_presigned_url_sync(
        self, object_name: str, expiration: int = 3600, bucket_name: str | None = None
    ) -> str:
        """
        Synchronous version of generate_presigned_url to be run in thread pool.

        Args:
            object_name: S3 object name
            expiration: Time in seconds for the presigned URL to remain valid (default: 1 hour)
            bucket_name: S3 bucket name (optional, uses default if not provided)

        Returns:
            str: Presigned URL for the object
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            raise Exception("S3 client not initialized")

        try:
            bucket = bucket_name or self.bucket_name

            # For DigitalOcean Spaces and other S3-compatible services,
            # we might want to return the direct URL if the bucket is public
            if self.endpoint_url and "digitaloceanspaces.com" in self.endpoint_url:
                # For DigitalOcean Spaces, if the file is public, return direct URL
                direct_url = f"{self.endpoint_url.rstrip('/')}/{bucket}/{object_name}"
                logger.info(
                    f"Generated direct URL for DigitalOcean Spaces: {direct_url}"
                )
                return direct_url

            # Generate presigned URL for AWS S3 or other services
            presigned_url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": object_name},
                ExpiresIn=expiration,
            )

            logger.info(
                f"Generated presigned URL for {object_name} (expires in {expiration}s)"
            )
            return presigned_url

        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {object_name}: {e}")
            # Fallback to direct URL construction
            bucket = bucket_name or self.bucket_name
            if self.endpoint_url:
                fallback_url = f"{self.endpoint_url.rstrip('/')}/{bucket}/{object_name}"
            else:
                fallback_url = f"https://{bucket}.s3.amazonaws.com/{object_name}"

            logger.warning(f"Using fallback URL: {fallback_url}")
            return fallback_url

    async def generate_presigned_url(
        self, object_name: str, expiration: int = 3600, bucket_name: str | None = None
    ) -> str:
        """
        Generate a presigned URL for an S3 object (async version that uses thread pool).

        Args:
            object_name: S3 object name
            expiration: Time in seconds for the presigned URL to remain valid (default: 1 hour)
            bucket_name: S3 bucket name (optional, uses default if not provided)

        Returns:
            str: Presigned URL for the object
        """
        return await asyncio.get_event_loop().run_in_executor(
            self.executor,
            lambda: self._generate_presigned_url_sync(
                object_name, expiration, bucket_name
            ),
        )


# Create a singleton instance
s3_service = S3Service()
