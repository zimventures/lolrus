# lolrus User Guide

A desktop S3-compatible object storage browser.

## Table of Contents

- [Getting Started](#getting-started)
- [Managing Connections](#managing-connections)
- [Browsing Buckets](#browsing-buckets)
- [Working with Objects](#working-with-objects)
- [Uploading Files](#uploading-files)
- [Downloading Files](#downloading-files)
- [Deleting Objects](#deleting-objects)
- [Preview Panel](#preview-panel)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### Installation

Download the appropriate version for your platform from the [Releases](https://github.com/zimventures/lolrus/releases) page:

| Platform | File |
|----------|------|
| Windows (x64) | `lolrus-windows-x86_64.exe` |
| Linux (x64) | `lolrus-linux-x86_64` |
| macOS (Intel) | `lolrus-macos-intel.zip` |
| macOS (Apple Silicon) | `lolrus-macos-arm64.zip` |

**Windows:** Run the `.exe` file directly.

**Linux:** Make the file executable and run it:
```bash
chmod +x lolrus-linux-x86_64
./lolrus-linux-x86_64
```

**macOS:** Extract the zip file, move `lolrus.app` to Applications. On first run, right-click and select "Open" to bypass Gatekeeper.

### First Launch

When you first launch lolrus, you'll see an empty interface. To get started:

1. Click **New** to create your first connection
2. Configure your S3-compatible storage credentials
3. Select a bucket to browse

---

## Managing Connections

### Creating a Connection

1. Click the **New** button in the toolbar
2. Fill in the connection details:
   - **Connection Name**: A friendly name for this connection (e.g., "Production S3")
   - **Endpoint URL**: The S3-compatible endpoint URL
   - **Region**: The region for the storage (default: `us-east-1`)
   - **Access Key**: Your access key ID
   - **Secret Key**: Your secret access key

3. (Optional) Select a preset from the dropdown to auto-fill the endpoint URL for common providers
4. Click **Test Connection** to verify your credentials
5. Click **Save** to store the connection

### Supported Providers

lolrus includes presets for common S3-compatible providers:

- **Linode Object Storage** (Atlanta, Newark, Frankfurt, Singapore)
- **AWS S3** (us-east-1, us-west-2)
- **DigitalOcean Spaces** (NYC3, SFO3)
- **Backblaze B2** (us-west)
- **MinIO** (local development)
- **Cloudflare R2**

You can also enter any custom S3-compatible endpoint URL.

### Editing a Connection

1. Select the connection from the dropdown
2. Click **Edit**
3. Modify the settings as needed
4. Click **Save**

### Deleting a Connection

1. Select the connection from the dropdown
2. Click **Delete**
3. Confirm the deletion

### Credential Security

Your credentials are stored securely using your system's native keyring:

- **Windows**: Windows Credential Manager
- **macOS**: Keychain
- **Linux**: Secret Service (GNOME Keyring, KWallet, etc.)

Connection metadata (name, endpoint, region) is stored in a local JSON file, but your access keys and secret keys are never written to disk in plaintext.

---

## Browsing Buckets

### Selecting a Bucket

1. First, select a connection from the **Connection** dropdown
2. Once connected, the **Bucket** dropdown will populate with available buckets
3. Select a bucket to view its contents

### Navigating Folders

S3 doesn't have true folders, but lolrus displays objects with common prefixes as navigable folders.

- **Enter a folder**: Click on a folder name (prefixed with a folder icon)
- **Go up**: Click the **Go Up** button or edit the path directly
- **Direct navigation**: Type a path in the **Path** input and press Enter

### Sorting

Click any column header to sort by that column:

- **Name**: Alphabetical order
- **Size**: By file size
- **Last Modified**: By modification date
- **Storage Class**: By storage class

Click again to reverse the sort order. An arrow indicator shows the current sort direction.

### Refreshing

Click **Refresh** to reload the current view and see any changes made outside of lolrus.

---

## Working with Objects

### Selecting Objects

- **Single selection**: Click the checkbox next to an object
- **Multiple selection**: Check multiple checkboxes

The selection count is displayed in the toolbar.

### Context Menu

Right-click any object to access the context menu:

- **Preview**: Open the preview panel for this object
- **Download**: Download to a selected folder
- **Copy URL**: Copy the full URL to clipboard
- **Copy Key**: Copy the object key to clipboard
- **Rename**: Rename the object (creates a copy with new name, then deletes original)
- **Delete**: Delete this object
- **Properties**: View detailed object metadata

### Object Properties

The Properties dialog shows:

- Name and full key path
- File size
- Last modified date
- Content type (MIME type)
- Storage class
- ETag (content hash)

---

## Uploading Files

### Using the Upload Button

1. Navigate to the destination folder in your bucket
2. Click **Upload**
3. Select one or more files from the file picker
4. Files will upload with progress tracking

### Drag and Drop (Windows only)

1. Navigate to the destination folder
2. Drag files from Windows Explorer onto the lolrus window
3. Files will upload automatically

**Note**: Directory uploads are not supported. Only individual files can be uploaded.

### Upload Progress

During upload, a progress bar appears in the status bar showing:

- Current file being uploaded
- Bytes transferred / total bytes

---

## Downloading Files

### Download Selected

1. Select one or more objects using the checkboxes
2. Click **Download**
3. Choose a destination folder
4. Files will download with progress tracking

### Download from Context Menu

1. Right-click an object
2. Select **Download**
3. Choose a destination folder

### Download Progress

The progress bar shows download progress for the current file.

---

## Deleting Objects

### Delete Selected

1. Select objects using the checkboxes
2. Click **Delete Selected**
3. Confirm the deletion

### Delete from Context Menu

1. Right-click an object
2. Select **Delete**
3. Confirm the deletion

### Empty Bucket

The **Empty Bucket** button deletes ALL objects in the current bucket. This is useful for deprovisioning buckets that must be empty before deletion.

**Warning**: This operation is irreversible! You must type the exact bucket name to confirm.

1. Click **Empty Bucket**
2. Read the warning carefully
3. Type the bucket name exactly as shown
4. Click **Confirm**

---

## Preview Panel

lolrus can preview certain file types without downloading them.

### Supported Preview Types

**Text Files**
- Source code: `.py`, `.js`, `.ts`, `.java`, `.c`, `.cpp`, `.go`, `.rs`, `.rb`, `.php`
- Web: `.html`, `.css`, `.jsx`, `.tsx`, `.vue`, `.svelte`
- Data: `.json`, `.xml`, `.csv`, `.yaml`, `.yml`
- Config: `.ini`, `.cfg`, `.toml`
- Documents: `.txt`, `.md`, `.log`
- Scripts: `.sh`, `.bat`, `.ps1`, `.sql`

**Images**
- `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`

**Archives** (shows file listing)
- `.zip`, `.tar`, `.tar.gz`, `.tgz`, `.gz`

### Using the Preview Panel

1. Click on any previewable object in the list
2. The preview panel opens on the right side
3. Click **X** to close the preview panel

### Preview Limitations

- Text files larger than 100KB are truncated
- Images are scaled to fit the preview panel
- Archive listings are limited to 500 entries
- Binary files and unsupported formats cannot be previewed

---

## Log Console

### Viewing Logs

Click **Logs** in the toolbar to toggle the log console. The console shows:

- Connection events
- File operations (uploads, downloads, deletes)
- Errors and warnings
- Timestamps for all events

### Log Actions

- **Copy**: Copy all logs to clipboard
- **Clear**: Clear the log history

### Resizing

Drag the top edge of the log console to resize it.

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Go Up | Click "Go Up" button |
| Refresh | Click "Refresh" button |

---

## Troubleshooting

### Connection Failed

- Verify your endpoint URL is correct
- Check that your access key and secret key are valid
- Ensure the region matches your bucket's region
- Check your network connection and firewall settings

### Cannot See Buckets

- Your credentials may not have `ListBuckets` permission
- Some providers require bucket names to be specified explicitly

### Upload/Download Fails

- Check that you have the necessary permissions on the bucket
- Verify you have sufficient disk space for downloads
- Large files may timeout on slow connections

### Preview Not Available

- The file type may not be supported for preview
- The file may exceed the size limit for preview
- Check the log console for specific error messages

### Credentials Not Saved

- Ensure your system keyring is properly configured
- On Linux, you may need `gnome-keyring` or `kwallet` installed
- Try running the application with elevated permissions

### Application Won't Start

**Windows**: Ensure you have the Visual C++ Redistributable installed.

**Linux**: Install required dependencies:
```bash
sudo apt-get install libgl1 libsecret-1-0
```

**macOS**: Right-click the app and select "Open" to bypass Gatekeeper on first run.

---

## Getting Help

- **GitHub Issues**: [github.com/zimventures/lolrus/issues](https://github.com/zimventures/lolrus/issues)
- **Source Code**: [github.com/zimventures/lolrus](https://github.com/zimventures/lolrus)

---

*I has a bucket!* 🦭
