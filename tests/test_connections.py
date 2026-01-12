"""
Tests for the connection management module.
"""

import json
from unittest.mock import patch

from lolrus.connections import KEYRING_SERVICE, Connection, ConnectionManager


class TestConnection:
    """Tests for Connection dataclass."""

    def test_connection_default_region(self):
        """Test connection defaults to us-east-1 region."""
        conn = Connection(name="test", endpoint_url="https://example.com")
        assert conn.region == "us-east-1"

    def test_connection_default_credentials(self):
        """Test connection credentials default to empty strings."""
        conn = Connection(name="test", endpoint_url="https://example.com")
        assert conn.access_key == ""
        assert conn.secret_key == ""

    def test_connection_to_dict_excludes_credentials(self):
        """Test to_dict excludes sensitive credentials."""
        conn = Connection(
            name="test",
            endpoint_url="https://example.com",
            region="eu-west-1",
            access_key="secret-access",
            secret_key="secret-key",
        )
        data = conn.to_dict()

        assert data["name"] == "test"
        assert data["endpoint_url"] == "https://example.com"
        assert data["region"] == "eu-west-1"
        assert "access_key" not in data
        assert "secret_key" not in data

    def test_connection_from_dict_basic(self):
        """Test from_dict creates connection from dictionary."""
        data = {
            "name": "my-conn",
            "endpoint_url": "https://s3.amazonaws.com",
            "region": "ap-northeast-1",
        }
        conn = Connection.from_dict(data)

        assert conn.name == "my-conn"
        assert conn.endpoint_url == "https://s3.amazonaws.com"
        assert conn.region == "ap-northeast-1"

    def test_connection_from_dict_default_region(self):
        """Test from_dict uses default region when not specified."""
        data = {
            "name": "test",
            "endpoint_url": "https://example.com",
        }
        conn = Connection.from_dict(data)
        assert conn.region == "us-east-1"


class TestConnectionManager:
    """Tests for ConnectionManager."""

    def test_creates_config_directory(self, tmp_path):
        """Test ConnectionManager creates config directory if missing."""
        config_dir = tmp_path / "config" / "lolrus"
        assert not config_dir.exists()

        ConnectionManager(config_dir=config_dir)

        assert config_dir.exists()

    def test_loads_existing_connections(self, tmp_path):
        """Test ConnectionManager loads connections from existing file."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        connections_file = config_dir / "connections.json"

        connections_file.write_text(json.dumps({
            "connections": [
                {"name": "conn1", "endpoint_url": "https://example1.com", "region": "us-east-1"},
                {"name": "conn2", "endpoint_url": "https://example2.com", "region": "eu-west-1"},
            ]
        }))

        manager = ConnectionManager(config_dir=config_dir)
        connections = manager.list_connections()

        assert len(connections) == 2
        names = [c.name for c in connections]
        assert "conn1" in names
        assert "conn2" in names

    def test_handles_corrupted_config_file(self, tmp_path):
        """Test ConnectionManager handles corrupted JSON gracefully."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        connections_file = config_dir / "connections.json"
        connections_file.write_text("{ invalid json }")

        manager = ConnectionManager(config_dir=config_dir)
        connections = manager.list_connections()

        assert len(connections) == 0

    def test_handles_missing_config_file(self, tmp_path):
        """Test ConnectionManager handles missing config file."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        manager = ConnectionManager(config_dir=config_dir)
        connections = manager.list_connections()

        assert len(connections) == 0

    @patch("lolrus.connections.keyring")
    def test_save_connection_stores_in_keyring(self, mock_keyring, tmp_path):
        """Test save_connection stores credentials in keyring."""
        config_dir = tmp_path / "config"
        manager = ConnectionManager(config_dir=config_dir)

        conn = Connection(
            name="test-conn",
            endpoint_url="https://example.com",
            region="us-east-1",
            access_key="my-access-key",
            secret_key="my-secret-key",
        )
        manager.save_connection(conn)

        # Verify keyring was called
        assert mock_keyring.set_password.call_count == 2
        mock_keyring.set_password.assert_any_call(
            KEYRING_SERVICE, "test-conn:access_key", "my-access-key"
        )
        mock_keyring.set_password.assert_any_call(
            KEYRING_SERVICE, "test-conn:secret_key", "my-secret-key"
        )

        # Verify connection metadata was saved
        connections = manager.list_connections()
        assert len(connections) == 1
        assert connections[0].name == "test-conn"

    @patch("lolrus.connections.keyring")
    def test_get_connection_loads_credentials(self, mock_keyring, tmp_path):
        """Test get_connection loads credentials from keyring."""
        mock_keyring.get_password.side_effect = lambda service, key: {
            "test-conn:access_key": "loaded-access",
            "test-conn:secret_key": "loaded-secret",
        }.get(key)

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        connections_file = config_dir / "connections.json"
        connections_file.write_text(json.dumps({
            "connections": [
                {"name": "test-conn", "endpoint_url": "https://example.com", "region": "us-east-1"},
            ]
        }))

        manager = ConnectionManager(config_dir=config_dir)
        conn = manager.get_connection("test-conn", load_credentials=True)

        assert conn is not None
        assert conn.access_key == "loaded-access"
        assert conn.secret_key == "loaded-secret"

    @patch("lolrus.connections.keyring")
    def test_get_connection_without_credentials(self, mock_keyring, tmp_path):
        """Test get_connection can skip loading credentials."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        connections_file = config_dir / "connections.json"
        connections_file.write_text(json.dumps({
            "connections": [
                {"name": "test-conn", "endpoint_url": "https://example.com"},
            ]
        }))

        manager = ConnectionManager(config_dir=config_dir)
        conn = manager.get_connection("test-conn", load_credentials=False)

        assert conn is not None
        assert conn.access_key == ""
        assert conn.secret_key == ""
        mock_keyring.get_password.assert_not_called()

    def test_get_connection_not_found(self, tmp_path):
        """Test get_connection returns None for nonexistent connection."""
        config_dir = tmp_path / "config"
        manager = ConnectionManager(config_dir=config_dir)

        conn = manager.get_connection("nonexistent")
        assert conn is None

    @patch("lolrus.connections.keyring")
    def test_delete_connection_removes_from_keyring(self, mock_keyring, tmp_path):
        """Test delete_connection removes credentials from keyring."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        connections_file = config_dir / "connections.json"
        connections_file.write_text(json.dumps({
            "connections": [
                {"name": "test-conn", "endpoint_url": "https://example.com"},
            ]
        }))

        manager = ConnectionManager(config_dir=config_dir)
        result = manager.delete_connection("test-conn")

        assert result is True
        assert mock_keyring.delete_password.call_count == 2
        mock_keyring.delete_password.assert_any_call(KEYRING_SERVICE, "test-conn:access_key")
        mock_keyring.delete_password.assert_any_call(KEYRING_SERVICE, "test-conn:secret_key")

        # Verify connection was removed from list
        connections = manager.list_connections()
        assert len(connections) == 0

    def test_delete_connection_not_found(self, tmp_path):
        """Test delete_connection returns False for nonexistent connection."""
        config_dir = tmp_path / "config"
        manager = ConnectionManager(config_dir=config_dir)

        result = manager.delete_connection("nonexistent")
        assert result is False

    @patch("lolrus.connections.keyring")
    def test_delete_connection_handles_keyring_error(self, mock_keyring, tmp_path):
        """Test delete_connection handles keyring errors gracefully."""
        import keyring.errors
        mock_keyring.errors = keyring.errors
        mock_keyring.delete_password.side_effect = keyring.errors.PasswordDeleteError()

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        connections_file = config_dir / "connections.json"
        connections_file.write_text(json.dumps({
            "connections": [
                {"name": "test-conn", "endpoint_url": "https://example.com"},
            ]
        }))

        manager = ConnectionManager(config_dir=config_dir)
        result = manager.delete_connection("test-conn")

        # Should still succeed even if keyring deletion fails
        assert result is True
        assert len(manager.list_connections()) == 0

    @patch("lolrus.connections.keyring")
    def test_rename_connection_success(self, mock_keyring, tmp_path):
        """Test rename_connection successfully renames a connection."""
        mock_keyring.get_password.side_effect = lambda service, key: {
            "old-name:access_key": "access",
            "old-name:secret_key": "secret",
        }.get(key)

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        connections_file = config_dir / "connections.json"
        connections_file.write_text(json.dumps({
            "connections": [
                {"name": "old-name", "endpoint_url": "https://example.com"},
            ]
        }))

        manager = ConnectionManager(config_dir=config_dir)
        result = manager.rename_connection("old-name", "new-name")

        assert result is True
        connections = manager.list_connections()
        names = [c.name for c in connections]
        assert "new-name" in names
        assert "old-name" not in names

    def test_rename_connection_old_not_found(self, tmp_path):
        """Test rename_connection returns False if old name not found."""
        config_dir = tmp_path / "config"
        manager = ConnectionManager(config_dir=config_dir)

        result = manager.rename_connection("nonexistent", "new-name")
        assert result is False

    @patch("lolrus.connections.keyring")
    def test_rename_connection_new_name_exists(self, mock_keyring, tmp_path):
        """Test rename_connection returns False if new name already exists."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        connections_file = config_dir / "connections.json"
        connections_file.write_text(json.dumps({
            "connections": [
                {"name": "conn1", "endpoint_url": "https://example1.com"},
                {"name": "conn2", "endpoint_url": "https://example2.com"},
            ]
        }))

        manager = ConnectionManager(config_dir=config_dir)
        result = manager.rename_connection("conn1", "conn2")

        assert result is False
        # Verify both connections still exist
        connections = manager.list_connections()
        assert len(connections) == 2

    def test_list_connections_returns_all(self, tmp_path):
        """Test list_connections returns all saved connections."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        connections_file = config_dir / "connections.json"
        connections_file.write_text(json.dumps({
            "connections": [
                {"name": "conn1", "endpoint_url": "https://example1.com"},
                {"name": "conn2", "endpoint_url": "https://example2.com"},
                {"name": "conn3", "endpoint_url": "https://example3.com"},
            ]
        }))

        manager = ConnectionManager(config_dir=config_dir)
        connections = manager.list_connections()

        assert len(connections) == 3


class TestKeyringKeyFormat:
    """Tests for keyring key generation."""

    def test_keyring_key_format(self, tmp_path):
        """Test _keyring_key generates correct format."""
        config_dir = tmp_path / "config"
        manager = ConnectionManager(config_dir=config_dir)

        access_key = manager._keyring_key("my-connection", "access_key")
        secret_key = manager._keyring_key("my-connection", "secret_key")

        assert access_key == "my-connection:access_key"
        assert secret_key == "my-connection:secret_key"

    def test_keyring_key_special_characters(self, tmp_path):
        """Test _keyring_key handles special characters in connection name."""
        config_dir = tmp_path / "config"
        manager = ConnectionManager(config_dir=config_dir)

        key = manager._keyring_key("My Connection (Test)", "access_key")
        assert key == "My Connection (Test):access_key"


class TestConnectionPersistence:
    """Tests for connection persistence to disk."""

    @patch("lolrus.connections.keyring")
    def test_connections_persisted_to_json(self, mock_keyring, tmp_path):
        """Test connections are persisted to JSON file."""
        config_dir = tmp_path / "config"
        manager = ConnectionManager(config_dir=config_dir)

        conn = Connection(
            name="persisted",
            endpoint_url="https://example.com",
            region="eu-central-1",
            access_key="key",
            secret_key="secret",
        )
        manager.save_connection(conn)

        # Read the file directly
        connections_file = config_dir / "connections.json"
        data = json.loads(connections_file.read_text())

        assert len(data["connections"]) == 1
        assert data["connections"][0]["name"] == "persisted"
        assert data["connections"][0]["endpoint_url"] == "https://example.com"
        assert data["connections"][0]["region"] == "eu-central-1"
        # Credentials should not be in the file
        assert "access_key" not in data["connections"][0]
        assert "secret_key" not in data["connections"][0]

    @patch("lolrus.connections.keyring")
    def test_connections_survive_reload(self, mock_keyring, tmp_path):
        """Test connections survive manager reload."""
        config_dir = tmp_path / "config"

        # Create and save connection
        manager1 = ConnectionManager(config_dir=config_dir)
        conn = Connection(
            name="survivor",
            endpoint_url="https://example.com",
            access_key="key",
            secret_key="secret",
        )
        manager1.save_connection(conn)

        # Create new manager instance (simulates app restart)
        manager2 = ConnectionManager(config_dir=config_dir)
        connections = manager2.list_connections()

        assert len(connections) == 1
        assert connections[0].name == "survivor"
