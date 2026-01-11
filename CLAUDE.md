# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

lolrus is a desktop S3-compatible object storage browser built with DearPyGui. It supports any S3-compatible provider (AWS, Linode, DigitalOcean, Backblaze B2, MinIO, Cloudflare R2, etc.) with secure credential storage via the system keyring.

## Development Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run the application
python -m lolrus
# or simply:
lolrus

# Lint
ruff check src/

# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_s3_client.py -v

# Run a specific test
pytest tests/test_s3_client.py::TestS3Object::test_name_extraction -v

# Build executable
pyinstaller lolrus.spec --clean
```

## Architecture

### Module Structure

- **`app.py`** - Main GUI application using DearPyGui. Contains `LolrusApp` class that manages the render loop, UI creation, and orchestrates all user interactions. Runs a custom main loop that calls `_update_progress()` each frame to update async operation status.

- **`s3_client.py`** - boto3 wrapper with async operation support. `S3Client` uses a `ThreadPoolExecutor` (4 workers) to run S3 operations in background threads, returning `AsyncOperation` objects for progress tracking. Sync methods (`list_buckets`, `list_objects`) are used for quick calls; async methods (`*_async`) are used for potentially slow operations.

- **`connections.py`** - Connection management with secure credential storage. `ConnectionManager` stores connection metadata (name, endpoint, region) in `~/.config/lolrus/connections.json` while credentials are stored in the system keyring via the `keyring` library.

### Key Patterns

- **Async Operations**: Long-running S3 operations return an `AsyncOperation` dataclass that tracks progress. The UI polls these in the render loop via `_update_progress()`.

- **Credential Security**: Credentials are never stored in plaintext. The `Connection.to_dict()` method explicitly excludes `access_key` and `secret_key`; these are stored/retrieved via keyring only when needed.

- **UI Tag System**: DearPyGui elements are referenced by string tags (e.g., `TAG_BUCKET_COMBO`, `TAG_OBJECT_TABLE`). Modal dialogs are created/destroyed dynamically using `dpg.does_item_exist()` checks.

## Configuration

- **Ruff**: Line length 160, targets Python 3.10+, ignores E501 (line length handled by line-length setting)
- **pytest**: Test discovery in `tests/`, source in `src/`
