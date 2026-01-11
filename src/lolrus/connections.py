"""
Connection management with secure credential storage.

Uses the system keyring to store secrets securely.
"""

import contextlib
import json
from dataclasses import dataclass
from pathlib import Path

import keyring

APP_NAME = "lolrus"
KEYRING_SERVICE = "lolrus-s3-browser"


@dataclass
class Connection:
    """A saved S3 connection."""

    name: str
    endpoint_url: str
    region: str = "us-east-1"

    # Note: access_key and secret_key are stored in keyring, not here
    # These fields are only populated when loading for use
    access_key: str = ""
    secret_key: str = ""

    def to_dict(self) -> dict:
        """Convert to dict for storage (excludes secrets)."""
        return {
            "name": self.name,
            "endpoint_url": self.endpoint_url,
            "region": self.region,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Connection":
        """Create from dict."""
        return cls(
            name=data["name"],
            endpoint_url=data["endpoint_url"],
            region=data.get("region", "us-east-1"),
        )


class ConnectionManager:
    """
    Manages saved S3 connections with secure credential storage.

    Connection metadata (name, endpoint, region) is stored in a JSON file.
    Credentials (access_key, secret_key) are stored in the system keyring.
    """

    def __init__(self, config_dir: Path | None = None):
        """
        Initialize the connection manager.

        Args:
            config_dir: Directory to store config. Defaults to ~/.config/lolrus
        """
        if config_dir is None:
            config_dir = Path.home() / ".config" / APP_NAME

        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.connections_file = self.config_dir / "connections.json"

        self._connections: dict[str, Connection] = {}
        self._load()

    def _load(self) -> None:
        """Load connections from disk."""
        if self.connections_file.exists():
            try:
                with open(self.connections_file) as f:
                    data = json.load(f)
                    for conn_data in data.get("connections", []):
                        conn = Connection.from_dict(conn_data)
                        self._connections[conn.name] = conn
            except (json.JSONDecodeError, KeyError):
                # Corrupted file, start fresh
                self._connections = {}

    def _save(self) -> None:
        """Save connections to disk."""
        data = {"connections": [c.to_dict() for c in self._connections.values()]}
        with open(self.connections_file, "w") as f:
            json.dump(data, f, indent=2)

    def _keyring_key(self, connection_name: str, field: str) -> str:
        """Generate a keyring key for a connection's credential field."""
        return f"{connection_name}:{field}"

    def list_connections(self) -> list[Connection]:
        """List all saved connections (without credentials loaded)."""
        return list(self._connections.values())

    def get_connection(self, name: str, load_credentials: bool = True) -> Connection | None:
        """
        Get a connection by name.

        Args:
            name: Connection name
            load_credentials: Whether to load credentials from keyring

        Returns:
            Connection or None if not found
        """
        conn = self._connections.get(name)
        if conn is None:
            return None

        if load_credentials:
            # Load credentials from keyring
            access_key = keyring.get_password(KEYRING_SERVICE, self._keyring_key(name, "access_key"))
            secret_key = keyring.get_password(KEYRING_SERVICE, self._keyring_key(name, "secret_key"))

            # Return a copy with credentials populated
            return Connection(
                name=conn.name,
                endpoint_url=conn.endpoint_url,
                region=conn.region,
                access_key=access_key or "",
                secret_key=secret_key or "",
            )

        return conn

    def save_connection(self, connection: Connection) -> None:
        """
        Save a connection.

        Stores metadata in JSON and credentials in keyring.

        Args:
            connection: Connection to save (must have credentials populated)
        """
        # Store credentials in keyring
        if connection.access_key:
            keyring.set_password(
                KEYRING_SERVICE,
                self._keyring_key(connection.name, "access_key"),
                connection.access_key,
            )
        if connection.secret_key:
            keyring.set_password(
                KEYRING_SERVICE,
                self._keyring_key(connection.name, "secret_key"),
                connection.secret_key,
            )

        # Store metadata (without credentials)
        self._connections[connection.name] = Connection(
            name=connection.name,
            endpoint_url=connection.endpoint_url,
            region=connection.region,
        )
        self._save()

    def delete_connection(self, name: str) -> bool:
        """
        Delete a connection.

        Args:
            name: Connection name to delete

        Returns:
            True if deleted, False if not found
        """
        if name not in self._connections:
            return False

        # Remove from keyring
        with contextlib.suppress(keyring.errors.PasswordDeleteError):
            keyring.delete_password(KEYRING_SERVICE, self._keyring_key(name, "access_key"))
        with contextlib.suppress(keyring.errors.PasswordDeleteError):
            keyring.delete_password(KEYRING_SERVICE, self._keyring_key(name, "secret_key"))

        # Remove from storage
        del self._connections[name]
        self._save()
        return True

    def rename_connection(self, old_name: str, new_name: str) -> bool:
        """
        Rename a connection.

        Args:
            old_name: Current connection name
            new_name: New connection name

        Returns:
            True if renamed, False if old_name not found or new_name exists
        """
        if old_name not in self._connections or new_name in self._connections:
            return False

        # Get full connection with credentials
        conn = self.get_connection(old_name, load_credentials=True)
        if conn is None:
            return False

        # Save with new name
        conn.name = new_name
        self.save_connection(conn)

        # Delete old
        self.delete_connection(old_name)
        return True


# Common S3-compatible endpoints for quick setup
COMMON_ENDPOINTS = {
    "Linode (Atlanta)": "https://us-southeast-1.linodeobjects.com",
    "Linode (Newark)": "https://us-east-1.linodeobjects.com",
    "Linode (Frankfurt)": "https://eu-central-1.linodeobjects.com",
    "Linode (Singapore)": "https://ap-south-1.linodeobjects.com",
    "AWS S3 (us-east-1)": "https://s3.us-east-1.amazonaws.com",
    "AWS S3 (us-west-2)": "https://s3.us-west-2.amazonaws.com",
    "DigitalOcean (NYC3)": "https://nyc3.digitaloceanspaces.com",
    "DigitalOcean (SFO3)": "https://sfo3.digitaloceanspaces.com",
    "Backblaze B2 (us-west)": "https://s3.us-west-004.backblazeb2.com",
    "MinIO (local)": "http://localhost:9000",
    "Cloudflare R2": "https://<account_id>.r2.cloudflarestorage.com",
}
