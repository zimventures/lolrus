# Screenshots

This directory contains screenshots for the README documentation.

## Current Status

The current screenshots are **mockups** created with PIL/Pillow to demonstrate the UI layout. They provide a good visual reference but are not actual screenshots of the running application.

**Contributors:** We welcome actual screenshots! If you can run lolrus and capture real screenshots, please submit a PR to replace the mockups.

## Screenshot Requirements

Please capture the following screenshots at 1200x800 resolution (or higher):

### Static Screenshots

1. **01-main-window.png** - Main application window showing:
   - Connection dropdown (top) with a saved connection selected
   - Bucket dropdown showing an actual bucket name
   - Object browser table with real files and folders
   - Action buttons (Upload, Download, Delete, etc.)
   - Status bar showing selection info

2. **02-new-connection.png** - New Connection dialog showing:
   - Connection name field
   - Endpoint preset dropdown (expanded if possible)
   - Custom endpoint URL field populated
   - Access key and secret key fields (obscured for security)
   - Region field
   - Test Connection button

3. **03-bucket-browser.png** - Bucket browser showing:
   - Multiple files and folders in a realistic structure
   - Varied file sizes (KB to MB range)
   - Last modified dates and times
   - Different storage classes if available
   - Several items selected with checkboxes

4. **04-upload-progress.png** - File upload in progress showing:
   - Progress bar with actual progress (e.g., 60-70%)
   - Upload status message
   - Current file name being uploaded
   - Data transferred / Total size

5. **05-delete-confirm.png** - Delete confirmation dialog showing:
   - Warning icon
   - Number of objects to be deleted
   - Clear warning text
   - Cancel and Delete buttons

6. **06-empty-bucket.png** - Empty bucket warning dialog showing:
   - Danger/warning styling
   - Bucket name to be emptied
   - Text input field with bucket name typed in
   - Warning that action cannot be undone

### Animated GIF Workflows (Bonus)

Create these animated GIFs (30-60 seconds each) showing complete workflows:

1. **workflow-upload.gif** - Complete upload workflow (15-30 seconds):
   - Starting state: bucket browser with some files
   - Click Upload button
   - File picker dialog appears
   - Select 2-3 files
   - Progress dialog appears
   - Progress bar advances
   - Files appear in bucket list
   - Final state: new files visible

2. **workflow-connection.gif** - Creating a new connection (20-30 seconds):
   - Starting state: main window
   - Click New button
   - Dialog appears
   - Fill in connection name
   - Select endpoint preset from dropdown
   - Enter access key (show typing but obscure text)
   - Enter secret key (obscured)
   - Click Test Connection
   - Success message appears
   - Click Save
   - Return to main window with new connection selected

3. **workflow-navigation.gif** - Navigating folders (15-20 seconds):
   - Starting state: bucket root
   - Click into a folder
   - Show folder contents
   - Select multiple files with checkboxes
   - Click back to parent folder using ".."
   - Edit path directly to jump to a deep folder
   - Show folder contents

4. **workflow-delete.gif** - Deleting objects (10-15 seconds):
   - Select 2-3 files
   - Click Delete button
   - Confirmation dialog appears
   - Click Delete to confirm
   - Files disappear from list

## Capturing Screenshots

### Tools

**Screen capture (static):**
- Windows: Snipping Tool, Snip & Sketch (Win+Shift+S)
- macOS: Screenshot utility (Cmd+Shift+4)
- Linux: gnome-screenshot, Spectacle, Flameshot

**Screen recording (for GIFs):**
- Windows: **ScreenToGif** (recommended - easy to use, built-in editor)
- macOS: **Kap** (recommended), GIPHY Capture, QuickTime + converter
- Linux: **Peek** (recommended), gifski, SimpleScreenRecorder + converter
- Cross-platform: OBS Studio + ffmpeg to convert to GIF

### Best Practices

1. **Set up a clean test environment:**
   - Use a test S3 bucket with realistic but safe content
   - Create sample folders and files with descriptive names
   - Use file sizes that look realistic (mix of KB and MB)

2. **Capture at good resolution:**
   - Application window: 1200x800 or larger
   - For GIFs: Consider 1200x800 or 1000x700 to keep file size manageable

3. **Optimize file sizes:**
   - PNG screenshots: Compress to <500KB (use tools like pngquant, TinyPNG)
   - GIF animations: Target <3MB (use GIF optimization tools)
   - Keep frame rate moderate (10-15 fps is usually sufficient for UI demos)

4. **Timing for GIFs:**
   - Move deliberately but not slowly
   - Pause briefly (0.5-1s) after key actions to let viewers see the result
   - Add a brief pause at the end before looping

5. **Security considerations:**
   - Never show real access keys or secret keys
   - Use obviously fake credentials or obscure them
   - Use test bucket names that don't reveal sensitive information
   - Don't show real file names if they contain sensitive data

### Submission

1. Capture the screenshots/GIFs following the guidelines above
2. Replace the mockup files in this directory (keep the same filenames)
3. Verify the README.md images still render correctly
4. Submit a PR with a brief description of what you captured
5. Include a note about the S3 provider used for the screenshots (e.g., "Screenshots using MinIO local instance")

## Creating Mockup Screenshots

If you need to regenerate the mockup screenshots, run:

```bash
python scripts/create_mockup_screenshots.py
```

This will recreate the placeholder images in this directory.
