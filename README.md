# 🦭 lolrus

**I has a bucket!**

A desktop S3-compatible object storage browser built with [DearPyGui](https://github.com/hoffstadt/DearPyGui).

![lolrus meme](https://i.imgflip.com/1bij.jpg)

## Features

- 🪣 **Multi-provider support** - Connect to any S3-compatible storage (Linode, AWS, DigitalOcean, Backblaze B2, MinIO, Cloudflare R2, etc.)
- 🔐 **Secure credential storage** - Credentials are stored in your system's native keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- 📁 **Browse objects** - Navigate bucket contents with folder-style hierarchy
- ⬆️ **Upload files** - Upload files with progress tracking
- ⬇️ **Download files** - Download single or multiple files
- 🗑️ **Delete objects** - Single or bulk delete with confirmation
- 🔥 **Empty bucket** - Nuclear option to delete ALL objects (requires typing bucket name to confirm)
- 📊 **Async operations** - All long-running operations happen in the background with progress indication

## Installation

### Pre-built binaries

Download the latest release for your platform from the [Releases](https://github.com/zimventures/lolrus/releases) page.

| Platform | Download |
|----------|----------|
| Windows (x64) | `lolrus-windows-x86_64.exe` |
| Linux (x64) | `lolrus-linux-x86_64` |
| macOS (Intel) | `lolrus-macos-intel.zip` |
| macOS (Apple Silicon) | `lolrus-macos-arm64.zip` |

### From source

Requires Python 3.10+

```bash
# Clone the repository
git clone https://github.com/zimventures/lolrus.git
cd lolrus

# Install in development mode
pip install -e ".[dev]"

# Run
lolrus
```

## Usage

### Quick Start

1. Launch lolrus
2. Click **New** to create a connection
3. Select a preset endpoint or enter a custom S3-compatible URL
4. Enter your access key and secret key
5. Click **Test Connection** to verify
6. Click **Save**
7. Select your connection from the dropdown
8. Select a bucket to browse

### Connection Presets

lolrus includes presets for common S3-compatible providers:

- Linode Object Storage (multiple regions)
- AWS S3 (us-east-1, us-west-2)
- DigitalOcean Spaces
- Backblaze B2
- MinIO (local development)
- Cloudflare R2

### Emptying a Bucket

The "Empty Bucket" feature is designed for situations like deprovisioning infrastructure where you need to delete all objects before the bucket can be removed.

⚠️ **Warning:** This operation is irreversible. You must type the exact bucket name to confirm.

## Building

### Local build

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Build with PyInstaller
pyinstaller lolrus.spec --clean

# Output will be in dist/
```

### Cross-platform builds via GitHub Actions

Push a tag to trigger automated builds:

```bash
git tag v0.1.0
git push origin v0.1.0
```

This will create builds for Windows, Linux, and macOS (both Intel and Apple Silicon).

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run linter
ruff check src/

# Run tests
pytest tests/ -v

# Run the app
python -m lolrus
```

## Architecture

```
src/lolrus/
├── __init__.py       # Package metadata
├── __main__.py       # Entry point
├── app.py            # Main DearPyGui application
├── s3_client.py      # boto3 wrapper with async operations
└── connections.py    # Connection management with keyring storage
```

### Key Design Decisions

- **DearPyGui** - GPU-accelerated, pure Python GUI library with minimal dependencies
- **boto3** - AWS SDK provides excellent S3 compatibility
- **keyring** - System-native credential storage (no plaintext passwords)
- **ThreadPoolExecutor** - Background operations don't block the UI
- **PyInstaller** - Single-file executables for easy distribution

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Why "lolrus"?

[It's an old meme, but it checks out.](https://knowyourmeme.com/memes/lolrus)

---

*They be stealin' my bucket!* 🦭
