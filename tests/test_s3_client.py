"""
Tests for the S3 client wrapper.
"""

import threading
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from lolrus.s3_client import AsyncOperation, OperationStatus, S3Bucket, S3Client, S3Object


class TestS3Object:
    """Tests for S3Object dataclass."""

    def test_name_extraction(self):
        """Test extracting name from key."""
        obj = S3Object(
            key="folder/subfolder/file.txt",
            size=100,
            last_modified=datetime.now(),
            etag="abc123",
        )
        assert obj.name == "file.txt"

    def test_name_with_trailing_slash(self):
        """Test name extraction handles folder-like keys."""
        obj = S3Object(
            key="folder/subfolder/",
            size=0,
            last_modified=datetime.now(),
            etag="abc123",
        )
        assert obj.name == "subfolder"

    def test_is_folder(self):
        """Test folder detection."""
        folder = S3Object(
            key="folder/",
            size=0,
            last_modified=datetime.now(),
            etag="abc123",
        )
        file = S3Object(
            key="file.txt",
            size=100,
            last_modified=datetime.now(),
            etag="abc123",
        )
        assert folder.is_folder is True
        assert file.is_folder is False


class TestAsyncOperation:
    """Tests for AsyncOperation tracking."""

    def test_initial_state(self):
        """Test operation initial state."""
        op = AsyncOperation(
            id="test-1",
            description="Test operation",
            total_items=100,
        )
        assert op.status == OperationStatus.PENDING
        assert op.progress == 0.0
        assert op.completed_items == 0
        assert op.is_cancelled is False

    def test_cancellation(self):
        """Test cancellation request."""
        op = AsyncOperation(id="test-1", description="Test")
        assert op.is_cancelled is False
        op.cancel()
        assert op.is_cancelled is True


class TestS3Client:
    """Tests for S3Client."""

    @patch("lolrus.s3_client.boto3.client")
    def test_client_initialization(self, mock_boto_client):
        """Test client initializes boto3 correctly."""
        client = S3Client(
            endpoint_url="https://example.com",
            access_key="access",
            secret_key="secret",
            region="us-east-1",
        )

        mock_boto_client.assert_called_once()
        call_kwargs = mock_boto_client.call_args[1]
        assert call_kwargs["endpoint_url"] == "https://example.com"
        assert call_kwargs["aws_access_key_id"] == "access"
        assert call_kwargs["aws_secret_access_key"] == "secret"
        assert call_kwargs["region_name"] == "us-east-1"

        client.close()

    @patch("lolrus.s3_client.boto3.client")
    def test_test_connection_success(self, mock_boto_client):
        """Test successful connection test."""
        mock_s3 = MagicMock()
        mock_s3.list_buckets.return_value = {"Buckets": []}
        mock_boto_client.return_value = mock_s3

        client = S3Client(
            endpoint_url="https://example.com",
            access_key="access",
            secret_key="secret",
        )

        assert client.test_connection() is True
        mock_s3.list_buckets.assert_called_once()
        client.close()

    @patch("lolrus.s3_client.boto3.client")
    def test_list_buckets(self, mock_boto_client):
        """Test listing buckets."""
        mock_s3 = MagicMock()
        mock_s3.list_buckets.return_value = {
            "Buckets": [
                {"Name": "bucket1", "CreationDate": datetime(2024, 1, 1)},
                {"Name": "bucket2", "CreationDate": datetime(2024, 1, 2)},
            ]
        }
        mock_boto_client.return_value = mock_s3

        client = S3Client(
            endpoint_url="https://example.com",
            access_key="access",
            secret_key="secret",
        )

        buckets = client.list_buckets()

        assert len(buckets) == 2
        assert buckets[0].name == "bucket1"
        assert buckets[1].name == "bucket2"
        client.close()


class TestConnectionManager:
    """Tests for ConnectionManager."""

    def test_connection_to_dict(self):
        """Test connection serialization excludes secrets."""
        from lolrus.connections import Connection

        conn = Connection(
            name="test",
            endpoint_url="https://example.com",
            region="us-east-1",
            access_key="access",
            secret_key="secret",
        )

        data = conn.to_dict()

        assert data["name"] == "test"
        assert data["endpoint_url"] == "https://example.com"
        assert data["region"] == "us-east-1"
        assert "access_key" not in data
        assert "secret_key" not in data

    def test_connection_from_dict(self):
        """Test connection deserialization."""
        from lolrus.connections import Connection

        data = {
            "name": "test",
            "endpoint_url": "https://example.com",
            "region": "eu-west-1",
        }

        conn = Connection.from_dict(data)

        assert conn.name == "test"
        assert conn.endpoint_url == "https://example.com"
        assert conn.region == "eu-west-1"
        assert conn.access_key == ""
        assert conn.secret_key == ""


class TestS3ClientListObjects:
    """Tests for S3Client.list_objects method."""

    @patch("lolrus.s3_client.boto3.client")
    def test_list_objects_returns_objects_and_prefixes(self, mock_boto_client):
        """Test listing objects returns both objects and folder prefixes."""
        mock_s3 = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "Contents": [
                    {
                        "Key": "file1.txt",
                        "Size": 100,
                        "LastModified": datetime(2024, 1, 1),
                        "ETag": '"abc123"',
                        "StorageClass": "STANDARD",
                    },
                    {
                        "Key": "file2.txt",
                        "Size": 200,
                        "LastModified": datetime(2024, 1, 2),
                        "ETag": '"def456"',
                    },
                ],
                "CommonPrefixes": [
                    {"Prefix": "folder1/"},
                    {"Prefix": "folder2/"},
                ],
            }
        ]
        mock_s3.get_paginator.return_value = mock_paginator
        mock_boto_client.return_value = mock_s3

        client = S3Client(
            endpoint_url="https://example.com",
            access_key="access",
            secret_key="secret",
        )

        objects, prefixes = client.list_objects("test-bucket")

        assert len(objects) == 2
        assert objects[0].key == "file1.txt"
        assert objects[0].size == 100
        assert objects[1].key == "file2.txt"
        assert len(prefixes) == 2
        assert "folder1/" in prefixes
        assert "folder2/" in prefixes
        client.close()

    @patch("lolrus.s3_client.boto3.client")
    def test_list_objects_with_prefix(self, mock_boto_client):
        """Test listing objects with prefix filter."""
        mock_s3 = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "Contents": [
                    {
                        "Key": "folder/file.txt",
                        "Size": 100,
                        "LastModified": datetime(2024, 1, 1),
                        "ETag": '"abc123"',
                    },
                ],
                "CommonPrefixes": [],
            }
        ]
        mock_s3.get_paginator.return_value = mock_paginator
        mock_boto_client.return_value = mock_s3

        client = S3Client(
            endpoint_url="https://example.com",
            access_key="access",
            secret_key="secret",
        )

        objects, prefixes = client.list_objects("test-bucket", prefix="folder/")

        mock_paginator.paginate.assert_called_with(
            Bucket="test-bucket", Prefix="folder/", Delimiter="/"
        )
        assert len(objects) == 1
        assert objects[0].key == "folder/file.txt"
        client.close()

    @patch("lolrus.s3_client.boto3.client")
    def test_list_objects_empty_bucket(self, mock_boto_client):
        """Test listing objects in an empty bucket."""
        mock_s3 = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{}]  # No Contents or CommonPrefixes
        mock_s3.get_paginator.return_value = mock_paginator
        mock_boto_client.return_value = mock_s3

        client = S3Client(
            endpoint_url="https://example.com",
            access_key="access",
            secret_key="secret",
        )

        objects, prefixes = client.list_objects("empty-bucket")

        assert len(objects) == 0
        assert len(prefixes) == 0
        client.close()

    @patch("lolrus.s3_client.boto3.client")
    def test_list_objects_skips_prefix_itself(self, mock_boto_client):
        """Test that listing objects skips the prefix key itself."""
        mock_s3 = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "Contents": [
                    {
                        "Key": "folder/",  # The prefix itself
                        "Size": 0,
                        "LastModified": datetime(2024, 1, 1),
                        "ETag": '"abc"',
                    },
                    {
                        "Key": "folder/file.txt",
                        "Size": 100,
                        "LastModified": datetime(2024, 1, 1),
                        "ETag": '"def"',
                    },
                ],
            }
        ]
        mock_s3.get_paginator.return_value = mock_paginator
        mock_boto_client.return_value = mock_s3

        client = S3Client(
            endpoint_url="https://example.com",
            access_key="access",
            secret_key="secret",
        )

        objects, prefixes = client.list_objects("bucket", prefix="folder/")

        assert len(objects) == 1
        assert objects[0].key == "folder/file.txt"
        client.close()


class TestS3ClientGetObjectInfo:
    """Tests for S3Client.get_object_info method."""

    @patch("lolrus.s3_client.boto3.client")
    def test_get_object_info_returns_metadata(self, mock_boto_client):
        """Test get_object_info returns correct metadata."""
        mock_s3 = MagicMock()
        mock_s3.head_object.return_value = {
            "ContentType": "text/plain",
            "ContentLength": 1234,
            "LastModified": datetime(2024, 1, 1),
            "ETag": '"abc123"',
            "Metadata": {"custom": "value"},
            "StorageClass": "STANDARD",
        }
        mock_boto_client.return_value = mock_s3

        client = S3Client(
            endpoint_url="https://example.com",
            access_key="access",
            secret_key="secret",
        )

        info = client.get_object_info("bucket", "file.txt")

        assert info["content_type"] == "text/plain"
        assert info["content_length"] == 1234
        assert info["etag"] == "abc123"
        assert info["metadata"] == {"custom": "value"}
        assert info["storage_class"] == "STANDARD"
        mock_s3.head_object.assert_called_once_with(Bucket="bucket", Key="file.txt")
        client.close()


class TestS3ClientDownloadToMemory:
    """Tests for S3Client.download_object_to_memory method."""

    @patch("lolrus.s3_client.boto3.client")
    def test_download_object_to_memory_success(self, mock_boto_client):
        """Test downloading small object to memory."""
        mock_s3 = MagicMock()
        mock_s3.head_object.return_value = {"ContentLength": 100}
        mock_body = MagicMock()
        mock_body.read.return_value = b"test content"
        mock_s3.get_object.return_value = {"Body": mock_body}
        mock_boto_client.return_value = mock_s3

        client = S3Client(
            endpoint_url="https://example.com",
            access_key="access",
            secret_key="secret",
        )

        data = client.download_object_to_memory("bucket", "file.txt")

        assert data == b"test content"
        mock_s3.get_object.assert_called_once_with(Bucket="bucket", Key="file.txt")
        client.close()

    @patch("lolrus.s3_client.boto3.client")
    def test_download_object_to_memory_too_large(self, mock_boto_client):
        """Test downloading object that exceeds max size raises error."""
        mock_s3 = MagicMock()
        mock_s3.head_object.return_value = {"ContentLength": 100_000_000}  # 100MB
        mock_boto_client.return_value = mock_s3

        client = S3Client(
            endpoint_url="https://example.com",
            access_key="access",
            secret_key="secret",
        )

        with pytest.raises(ValueError) as exc_info:
            client.download_object_to_memory("bucket", "large-file.bin")

        assert "too large for preview" in str(exc_info.value)
        client.close()


class TestS3ClientConnectionFailure:
    """Tests for connection failure scenarios."""

    @patch("lolrus.s3_client.boto3.client")
    def test_test_connection_failure(self, mock_boto_client):
        """Test connection failure returns False."""
        mock_s3 = MagicMock()
        mock_s3.list_buckets.side_effect = ClientError(
            {"Error": {"Code": "InvalidAccessKeyId", "Message": "Invalid"}},
            "ListBuckets"
        )
        mock_boto_client.return_value = mock_s3

        client = S3Client(
            endpoint_url="https://example.com",
            access_key="invalid",
            secret_key="invalid",
        )

        assert client.test_connection() is False
        client.close()


class TestS3ClientAsyncOperations:
    """Tests for async operations."""

    @patch("lolrus.s3_client.boto3.client")
    def test_delete_objects_async_calls_callback(self, mock_boto_client):
        """Test delete_objects_async calls completion callback."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        client = S3Client(
            endpoint_url="https://example.com",
            access_key="access",
            secret_key="secret",
        )

        completed = threading.Event()
        result_op = None

        def on_complete(op):
            nonlocal result_op
            result_op = op
            completed.set()

        op = client.delete_objects_async(
            "bucket",
            ["key1", "key2"],
            on_complete=on_complete,
        )

        # Note: We don't check op.status == PENDING here because
        # the operation may complete before we can check (race condition)
        assert op.total_items == 2

        # Wait for completion
        completed.wait(timeout=5)

        assert result_op is not None
        assert result_op.status == OperationStatus.COMPLETED
        mock_s3.delete_objects.assert_called_once()
        client.close()

    @patch("lolrus.s3_client.boto3.client")
    def test_async_operation_progress_tracking(self, mock_boto_client):
        """Test async operations track progress correctly."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        client = S3Client(
            endpoint_url="https://example.com",
            access_key="access",
            secret_key="secret",
        )

        progress_updates = []
        completed = threading.Event()

        def on_progress(op):
            progress_updates.append(op.progress)

        def on_complete(op):
            completed.set()

        keys = [f"key{i}" for i in range(10)]
        op = client.delete_objects_async(
            "bucket",
            keys,
            on_progress=on_progress,
            on_complete=on_complete,
        )

        completed.wait(timeout=5)

        assert op.status == OperationStatus.COMPLETED
        assert op.progress == 1.0
        assert op.completed_items == 10
        client.close()

    @patch("lolrus.s3_client.boto3.client")
    def test_async_operation_cancellation(self, mock_boto_client):
        """Test async operation can be cancelled."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        client = S3Client(
            endpoint_url="https://example.com",
            access_key="access",
            secret_key="secret",
        )

        op = AsyncOperation(id="test", description="Test op")
        op.cancel()
        assert op.is_cancelled is True
        client.close()

    @patch("lolrus.s3_client.boto3.client")
    def test_empty_bucket_async_empty_bucket(self, mock_boto_client):
        """Test emptying an already empty bucket."""
        mock_s3 = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{}]  # No objects
        mock_s3.get_paginator.return_value = mock_paginator
        mock_boto_client.return_value = mock_s3

        client = S3Client(
            endpoint_url="https://example.com",
            access_key="access",
            secret_key="secret",
        )

        completed = threading.Event()
        result_op = None

        def on_complete(op):
            nonlocal result_op
            result_op = op
            completed.set()

        client.empty_bucket_async("empty-bucket", on_complete=on_complete)
        completed.wait(timeout=5)

        assert result_op.status == OperationStatus.COMPLETED
        assert result_op.total_items == 0
        mock_s3.delete_objects.assert_not_called()
        client.close()


class TestS3ObjectAdditional:
    """Additional tests for S3Object."""

    def test_storage_class_default(self):
        """Test storage class defaults to STANDARD."""
        obj = S3Object(
            key="file.txt",
            size=100,
            last_modified=datetime.now(),
            etag="abc",
        )
        assert obj.storage_class == "STANDARD"

    def test_root_level_file_name(self):
        """Test name extraction for root-level file."""
        obj = S3Object(
            key="readme.txt",
            size=100,
            last_modified=datetime.now(),
            etag="abc",
        )
        assert obj.name == "readme.txt"

    def test_deeply_nested_file_name(self):
        """Test name extraction for deeply nested file."""
        obj = S3Object(
            key="a/b/c/d/e/file.txt",
            size=100,
            last_modified=datetime.now(),
            etag="abc",
        )
        assert obj.name == "file.txt"


class TestS3BucketDataclass:
    """Tests for S3Bucket dataclass."""

    def test_bucket_creation_with_date(self):
        """Test bucket creation with creation date."""
        bucket = S3Bucket(name="test-bucket", creation_date=datetime(2024, 1, 1))
        assert bucket.name == "test-bucket"
        assert bucket.creation_date == datetime(2024, 1, 1)

    def test_bucket_creation_without_date(self):
        """Test bucket creation without creation date."""
        bucket = S3Bucket(name="test-bucket")
        assert bucket.name == "test-bucket"
        assert bucket.creation_date is None
