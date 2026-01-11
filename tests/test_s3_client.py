"""
Tests for the S3 client wrapper.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from lolrus.s3_client import S3Client, S3Object, S3Bucket, AsyncOperation, OperationStatus


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
