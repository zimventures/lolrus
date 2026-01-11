"""
S3 client wrapper with async operations.

All S3 operations run in a thread pool to keep the UI responsive.
"""

import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class OperationStatus(Enum):
    """Status of an async operation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class S3Object:
    """Represents an object in S3."""

    key: str
    size: int
    last_modified: datetime
    etag: str
    storage_class: str = "STANDARD"

    @property
    def name(self) -> str:
        """Get the object name (last part of key)."""
        return self.key.rstrip("/").split("/")[-1]

    @property
    def is_folder(self) -> bool:
        """Check if this represents a folder prefix."""
        return self.key.endswith("/")


@dataclass
class S3Bucket:
    """Represents an S3 bucket."""

    name: str
    creation_date: datetime | None = None


@dataclass
class AsyncOperation:
    """Tracks an async operation's progress."""

    id: str
    description: str
    status: OperationStatus = OperationStatus.PENDING
    progress: float = 0.0
    total_items: int = 0
    completed_items: int = 0
    error: str | None = None
    _cancelled: bool = False

    def cancel(self) -> None:
        """Request cancellation of this operation."""
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        return self._cancelled


class S3Client:
    """
    S3-compatible storage client with async operations.

    All operations that might take time run in a thread pool and
    report progress via callbacks.
    """

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
        log_callback: Callable[[str, str], None] | None = None,
    ):
        """
        Initialize the S3 client.

        Args:
            endpoint_url: S3-compatible endpoint (e.g., https://us-east-1.linodeobjects.com)
            access_key: Access key ID
            secret_key: Secret access key
            region: Region name (default: us-east-1)
            log_callback: Optional callback for logging (message, level)
        """
        self.endpoint_url = endpoint_url
        self.region = region
        self._log = log_callback or (lambda msg, level: None)

        # Configure boto3 with retries and timeouts
        config = Config(
            retries={"max_attempts": 3, "mode": "adaptive"},
            connect_timeout=10,
            read_timeout=30,
        )

        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=config,
        )

        # Thread pool for async operations
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="lolrus-s3")
        self._operations: dict[str, AsyncOperation] = {}
        self._operation_counter = 0
        self._lock = threading.Lock()

    def close(self) -> None:
        """Shutdown the client and thread pool."""
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _next_operation_id(self) -> str:
        """Generate a unique operation ID."""
        with self._lock:
            self._operation_counter += 1
            return f"op-{self._operation_counter}"

    # -------------------------------------------------------------------------
    # Synchronous operations (for quick calls)
    # -------------------------------------------------------------------------

    def test_connection(self) -> bool:
        """Test if the connection works by listing buckets."""
        try:
            self._client.list_buckets()
            return True
        except ClientError:
            return False

    def list_buckets(self) -> list[S3Bucket]:
        """List all buckets."""
        response = self._client.list_buckets()
        return [S3Bucket(name=b["Name"], creation_date=b.get("CreationDate")) for b in response.get("Buckets", [])]

    def list_objects(self, bucket: str, prefix: str = "", delimiter: str = "/") -> tuple[list[S3Object], list[str]]:
        """
        List objects in a bucket with optional prefix.

        Args:
            bucket: Bucket name
            prefix: Key prefix to filter by
            delimiter: Delimiter for "folder" grouping (default: /)

        Returns:
            Tuple of (objects, common_prefixes) where common_prefixes are "folders"
        """
        objects = []
        prefixes = []

        paginator = self._client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter=delimiter):
            # Get actual objects
            for obj in page.get("Contents", []):
                # Skip the prefix itself if it's listed
                if obj["Key"] == prefix:
                    continue
                objects.append(
                    S3Object(
                        key=obj["Key"],
                        size=obj["Size"],
                        last_modified=obj["LastModified"],
                        etag=obj["ETag"].strip('"'),
                        storage_class=obj.get("StorageClass", "STANDARD"),
                    )
                )

            # Get "folder" prefixes
            for p in page.get("CommonPrefixes", []):
                prefixes.append(p["Prefix"])

        return objects, prefixes

    def get_object_info(self, bucket: str, key: str) -> dict:
        """Get detailed metadata for an object."""
        response = self._client.head_object(Bucket=bucket, Key=key)
        return {
            "content_type": response.get("ContentType", "application/octet-stream"),
            "content_length": response.get("ContentLength", 0),
            "last_modified": response.get("LastModified"),
            "etag": response.get("ETag", "").strip('"'),
            "metadata": response.get("Metadata", {}),
            "storage_class": response.get("StorageClass", "STANDARD"),
        }

    def download_object_to_memory(self, bucket: str, key: str, max_size: int = 50_000_000) -> bytes:
        """
        Download object content to memory (with size limit).

        Args:
            bucket: Bucket name
            key: Object key
            max_size: Maximum file size to download (default 50MB)

        Returns:
            Object content as bytes

        Raises:
            ValueError: If object exceeds max_size
        """
        info = self.get_object_info(bucket, key)
        if info["content_length"] > max_size:
            raise ValueError(f"Object too large for preview: {info['content_length']} bytes (max: {max_size})")

        response = self._client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    # -------------------------------------------------------------------------
    # Async operations (for potentially slow calls)
    # -------------------------------------------------------------------------

    def delete_objects_async(
        self,
        bucket: str,
        keys: list[str],
        on_progress: Callable[[AsyncOperation], None] | None = None,
        on_complete: Callable[[AsyncOperation], None] | None = None,
    ) -> AsyncOperation:
        """
        Delete multiple objects asynchronously.

        Args:
            bucket: Bucket name
            keys: List of object keys to delete
            on_progress: Callback for progress updates
            on_complete: Callback when operation completes

        Returns:
            AsyncOperation tracking the deletion
        """
        op = AsyncOperation(
            id=self._next_operation_id(),
            description=f"Deleting {len(keys)} objects from {bucket}",
            total_items=len(keys),
        )
        self._operations[op.id] = op

        def do_delete():
            op.status = OperationStatus.RUNNING
            self._log(f"Starting delete of {len(keys)} objects", "DEBUG")
            try:
                # Delete in batches of 1000 (S3 limit)
                batch_size = 1000
                for i in range(0, len(keys), batch_size):
                    if op.is_cancelled:
                        op.status = OperationStatus.CANCELLED
                        break

                    batch = keys[i : i + batch_size]
                    delete_request = {"Objects": [{"Key": k} for k in batch], "Quiet": True}

                    self._client.delete_objects(Bucket=bucket, Delete=delete_request)
                    self._log(f"Deleted batch of {len(batch)} objects", "DEBUG")

                    op.completed_items += len(batch)
                    op.progress = op.completed_items / op.total_items

                    if on_progress:
                        on_progress(op)

                if op.status != OperationStatus.CANCELLED:
                    op.status = OperationStatus.COMPLETED
                    op.progress = 1.0
                self._log(f"Delete operation completed: {op.status.value}", "DEBUG")

            except Exception as e:
                op.status = OperationStatus.FAILED
                op.error = str(e)
                self._log(f"Delete failed: {e}", "ERROR")

            if on_complete:
                on_complete(op)

        self._executor.submit(do_delete)
        return op

    def download_object_async(
        self,
        bucket: str,
        key: str,
        local_path: str,
        on_progress: Callable[[AsyncOperation], None] | None = None,
        on_complete: Callable[[AsyncOperation], None] | None = None,
    ) -> AsyncOperation:
        """
        Download an object asynchronously.

        Args:
            bucket: Bucket name
            key: Object key
            local_path: Local file path to save to
            on_progress: Callback for progress updates
            on_complete: Callback when operation completes

        Returns:
            AsyncOperation tracking the download
        """
        op = AsyncOperation(
            id=self._next_operation_id(),
            description=f"Downloading {key}",
        )
        self._operations[op.id] = op

        def do_download():
            op.status = OperationStatus.RUNNING
            try:
                # Get object size first
                head = self._client.head_object(Bucket=bucket, Key=key)
                total_size = head.get("ContentLength", 0)
                op.total_items = total_size

                downloaded = 0

                def progress_callback(bytes_transferred):
                    nonlocal downloaded
                    if op.is_cancelled:
                        raise InterruptedError("Download cancelled")
                    downloaded += bytes_transferred
                    op.completed_items = downloaded
                    op.progress = downloaded / total_size if total_size > 0 else 1.0
                    if on_progress:
                        on_progress(op)

                self._client.download_file(bucket, key, local_path, Callback=progress_callback)

                op.status = OperationStatus.COMPLETED
                op.progress = 1.0

            except InterruptedError:
                op.status = OperationStatus.CANCELLED
            except ClientError as e:
                op.status = OperationStatus.FAILED
                op.error = str(e)

            if on_complete:
                on_complete(op)

        self._executor.submit(do_download)
        return op

    def upload_file_async(
        self,
        bucket: str,
        key: str,
        local_path: str,
        on_progress: Callable[[AsyncOperation], None] | None = None,
        on_complete: Callable[[AsyncOperation], None] | None = None,
    ) -> AsyncOperation:
        """
        Upload a file asynchronously.

        Args:
            bucket: Bucket name
            key: Object key to create
            local_path: Local file path to upload
            on_progress: Callback for progress updates
            on_complete: Callback when operation completes

        Returns:
            AsyncOperation tracking the upload
        """
        import os

        op = AsyncOperation(
            id=self._next_operation_id(),
            description=f"Uploading {os.path.basename(local_path)}",
        )
        self._operations[op.id] = op

        def do_upload():
            op.status = OperationStatus.RUNNING
            try:
                total_size = os.path.getsize(local_path)
                op.total_items = total_size

                uploaded = 0

                def progress_callback(bytes_transferred):
                    nonlocal uploaded
                    if op.is_cancelled:
                        raise InterruptedError("Upload cancelled")
                    uploaded += bytes_transferred
                    op.completed_items = uploaded
                    op.progress = uploaded / total_size if total_size > 0 else 1.0
                    if on_progress:
                        on_progress(op)

                self._client.upload_file(local_path, bucket, key, Callback=progress_callback)

                op.status = OperationStatus.COMPLETED
                op.progress = 1.0

            except InterruptedError:
                op.status = OperationStatus.CANCELLED
            except ClientError as e:
                op.status = OperationStatus.FAILED
                op.error = str(e)

            if on_complete:
                on_complete(op)

        self._executor.submit(do_upload)
        return op

    def empty_bucket_async(
        self,
        bucket: str,
        on_progress: Callable[[AsyncOperation], None] | None = None,
        on_complete: Callable[[AsyncOperation], None] | None = None,
    ) -> AsyncOperation:
        """
        Delete ALL objects in a bucket (nuke it).

        Args:
            bucket: Bucket name
            on_progress: Callback for progress updates
            on_complete: Callback when operation completes

        Returns:
            AsyncOperation tracking the deletion
        """
        op = AsyncOperation(
            id=self._next_operation_id(),
            description=f"Emptying bucket {bucket}",
        )
        self._operations[op.id] = op

        def do_empty():
            op.status = OperationStatus.RUNNING
            try:
                # First, count all objects
                paginator = self._client.get_paginator("list_objects_v2")
                all_keys = []

                for page in paginator.paginate(Bucket=bucket):
                    if op.is_cancelled:
                        op.status = OperationStatus.CANCELLED
                        if on_complete:
                            on_complete(op)
                        return

                    for obj in page.get("Contents", []):
                        all_keys.append(obj["Key"])

                op.total_items = len(all_keys)

                if len(all_keys) == 0:
                    op.status = OperationStatus.COMPLETED
                    op.progress = 1.0
                    if on_complete:
                        on_complete(op)
                    return

                # Delete in batches
                batch_size = 1000
                for i in range(0, len(all_keys), batch_size):
                    if op.is_cancelled:
                        op.status = OperationStatus.CANCELLED
                        break

                    batch = all_keys[i : i + batch_size]
                    delete_request = {"Objects": [{"Key": k} for k in batch], "Quiet": True}

                    self._client.delete_objects(Bucket=bucket, Delete=delete_request)

                    op.completed_items += len(batch)
                    op.progress = op.completed_items / op.total_items

                    if on_progress:
                        on_progress(op)

                if op.status != OperationStatus.CANCELLED:
                    op.status = OperationStatus.COMPLETED
                    op.progress = 1.0

            except ClientError as e:
                op.status = OperationStatus.FAILED
                op.error = str(e)

            if on_complete:
                on_complete(op)

        self._executor.submit(do_empty)
        return op

    def get_operation(self, operation_id: str) -> AsyncOperation | None:
        """Get an operation by ID."""
        return self._operations.get(operation_id)
