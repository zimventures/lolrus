#!/usr/bin/env python3
"""
Create mockup screenshots for the README.
These are placeholder images that demonstrate the UI layout.
Replace with actual screenshots once the application can be run.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Colors (DearPyGui-like dark theme)
BG_COLOR = (37, 37, 38)
HEADER_BG = (45, 45, 48)
BUTTON_BG = (62, 62, 66)
INPUT_BG = (60, 60, 60)
TEXT_COLOR = (255, 255, 255)
ACCENT_COLOR = (0, 119, 200)
TABLE_ALT_ROW = (50, 50, 50)

def create_main_window():
    """Create mockup of main application window."""
    img = Image.new('RGB', (1200, 800), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Title bar area
    draw.rectangle([0, 0, 1200, 30], fill=HEADER_BG)
    draw.text((10, 8), "lolrus v0.1.0 - I has a bucket!", fill=TEXT_COLOR)
    
    # Toolbar area
    y = 40
    draw.text((10, y), "Connection:", fill=TEXT_COLOR)
    draw.rectangle([100, y-2, 300, y+20], fill=INPUT_BG, outline=ACCENT_COLOR)
    draw.text((105, y), "My Linode Storage", fill=TEXT_COLOR)
    
    # New/Edit buttons
    draw.rectangle([320, y-2, 370, y+20], fill=BUTTON_BG, outline=ACCENT_COLOR)
    draw.text((328, y), "New", fill=TEXT_COLOR)
    draw.rectangle([380, y-2, 430, y+20], fill=BUTTON_BG, outline=ACCENT_COLOR)
    draw.text((385, y), "Edit", fill=TEXT_COLOR)
    
    # Bucket dropdown
    y = 75
    draw.text((10, y), "Bucket:", fill=TEXT_COLOR)
    draw.rectangle([100, y-2, 300, y+20], fill=INPUT_BG, outline=ACCENT_COLOR)
    draw.text((105, y), "my-awesome-bucket", fill=TEXT_COLOR)
    
    # Path input
    y = 110
    draw.text((10, y), "Path:", fill=TEXT_COLOR)
    draw.rectangle([100, y-2, 600, y+20], fill=INPUT_BG, outline=ACCENT_COLOR)
    draw.text((105, y), "/", fill=TEXT_COLOR)
    
    # Action buttons
    y = 145
    buttons = ["Upload", "Download", "Delete", "Refresh", "Empty Bucket"]
    x = 10
    for btn in buttons:
        width = len(btn) * 9 + 10
        draw.rectangle([x, y, x+width, y+25], fill=BUTTON_BG, outline=ACCENT_COLOR)
        draw.text((x+5, y+5), btn, fill=TEXT_COLOR)
        x += width + 10
    
    # Table header
    y = 185
    draw.rectangle([10, y, 1190, y+25], fill=HEADER_BG)
    draw.text((15, y+5), "☐ Name", fill=TEXT_COLOR)
    draw.text((400, y+5), "Size", fill=TEXT_COLOR)
    draw.text((550, y+5), "Last Modified", fill=TEXT_COLOR)
    draw.text((800, y+5), "Storage Class", fill=TEXT_COLOR)
    
    # Table rows
    y = 215
    rows = [
        ("📁 documents/", "", "", ""),
        ("📁 images/", "", "", ""),
        ("☐ readme.txt", "1.2 KB", "2024-01-15 10:30:00", "STANDARD"),
        ("☐ backup.zip", "45.6 MB", "2024-01-14 09:15:00", "STANDARD"),
        ("☐ report.pdf", "2.3 MB", "2024-01-13 16:45:00", "STANDARD"),
    ]
    
    for i, (name, size, modified, storage) in enumerate(rows):
        bg = TABLE_ALT_ROW if i % 2 else BG_COLOR
        draw.rectangle([10, y, 1190, y+25], fill=bg)
        draw.text((15, y+5), name, fill=TEXT_COLOR)
        draw.text((400, y+5), size, fill=TEXT_COLOR)
        draw.text((550, y+5), modified, fill=TEXT_COLOR)
        draw.text((800, y+5), storage, fill=TEXT_COLOR)
        y += 25
    
    # Status bar
    draw.rectangle([0, 770, 1200, 800], fill=HEADER_BG)
    draw.text((10, 778), "Ready | 3 objects selected", fill=TEXT_COLOR)
    
    img.save(os.path.join(OUTPUT_DIR, "01-main-window.png"))
    print("Created: 01-main-window.png")

def create_connection_dialog():
    """Create mockup of new connection dialog."""
    img = Image.new('RGB', (600, 500), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Dialog title
    draw.rectangle([0, 0, 600, 35], fill=HEADER_BG)
    draw.text((10, 10), "New Connection", fill=TEXT_COLOR)
    
    y = 50
    fields = [
        ("Connection Name:", "My S3 Storage"),
        ("Endpoint Preset:", "Linode - us-east-1 ▼"),
        ("Endpoint URL:", "https://us-east-1.linodeobjects.com"),
        ("Access Key ID:", "••••••••••••••••"),
        ("Secret Access Key:", "••••••••••••••••••••"),
        ("Region:", "us-east-1"),
    ]
    
    for label, value in fields:
        draw.text((20, y), label, fill=TEXT_COLOR)
        draw.rectangle([180, y-2, 570, y+20], fill=INPUT_BG, outline=ACCENT_COLOR)
        draw.text((185, y), value, fill=TEXT_COLOR)
        y += 40
    
    # Buttons at bottom
    y = 450
    draw.rectangle([20, y, 150, y+30], fill=BUTTON_BG, outline=ACCENT_COLOR)
    draw.text((35, y+8), "Test Connection", fill=TEXT_COLOR)
    
    draw.rectangle([390, y, 470, y+30], fill=BUTTON_BG, outline=ACCENT_COLOR)
    draw.text((410, y+8), "Cancel", fill=TEXT_COLOR)
    
    draw.rectangle([480, y, 560, y+30], fill=ACCENT_COLOR, outline=ACCENT_COLOR)
    draw.text((505, y+8), "Save", fill=TEXT_COLOR)
    
    img.save(os.path.join(OUTPUT_DIR, "02-new-connection.png"))
    print("Created: 02-new-connection.png")

def create_upload_progress():
    """Create mockup of upload progress."""
    img = Image.new('RGB', (1200, 800), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Copy main window elements from create_main_window
    draw.rectangle([0, 0, 1200, 30], fill=HEADER_BG)
    draw.text((10, 8), "lolrus v0.1.0 - I has a bucket!", fill=TEXT_COLOR)
    
    # Simplified toolbar
    y = 40
    draw.text((10, y), "Connection: My Linode Storage | Bucket: my-awesome-bucket", fill=TEXT_COLOR)
    
    # Table with files
    y = 150
    draw.rectangle([10, y, 1190, y+25], fill=HEADER_BG)
    draw.text((15, y+5), "Name", fill=TEXT_COLOR)
    
    y = 180
    files = ["document.pdf", "image.jpg", "data.csv"]
    for file in files:
        draw.text((15, y), f"📄 {file}", fill=TEXT_COLOR)
        y += 25
    
    # Progress bar overlay
    y = 350
    draw.rectangle([300, y-20, 900, y+120], fill=HEADER_BG, outline=ACCENT_COLOR, width=2)
    draw.text((450, y), "Uploading files...", fill=TEXT_COLOR)
    
    # Progress bar
    y += 30
    draw.rectangle([320, y, 880, y+30], fill=INPUT_BG, outline=ACCENT_COLOR)
    draw.rectangle([320, y, 680, y+30], fill=ACCENT_COLOR)  # 60% progress
    draw.text((550, y+7), "60%", fill=TEXT_COLOR)
    
    draw.text((320, y+40), "Uploading: image.jpg (2 of 3)", fill=TEXT_COLOR)
    draw.text((320, y+60), "1.2 MB / 2.0 MB", fill=TEXT_COLOR)
    
    img.save(os.path.join(OUTPUT_DIR, "04-upload-progress.png"))
    print("Created: 04-upload-progress.png")

def create_delete_confirm():
    """Create mockup of delete confirmation dialog."""
    img = Image.new('RGB', (500, 250), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Dialog title
    draw.rectangle([0, 0, 500, 35], fill=HEADER_BG)
    draw.text((10, 10), "Confirm Delete", fill=TEXT_COLOR)
    
    # Warning icon and text
    y = 60
    draw.text((50, y), "⚠️", fill=(255, 165, 0))  # Orange warning
    draw.text((100, y), "Are you sure you want to delete", fill=TEXT_COLOR)
    draw.text((100, y+25), "the selected 3 object(s)?", fill=TEXT_COLOR)
    draw.text((100, y+60), "This action cannot be undone.", fill=TEXT_COLOR)
    
    # Buttons
    y = 190
    draw.rectangle([250, y, 340, y+30], fill=BUTTON_BG, outline=ACCENT_COLOR)
    draw.text((275, y+8), "Cancel", fill=TEXT_COLOR)
    
    draw.rectangle([350, y, 470, y+30], fill=(180, 0, 0), outline=(200, 0, 0))
    draw.text((375, y+8), "Delete", fill=TEXT_COLOR)
    
    img.save(os.path.join(OUTPUT_DIR, "05-delete-confirm.png"))
    print("Created: 05-delete-confirm.png")

def create_empty_bucket_dialog():
    """Create mockup of empty bucket warning dialog."""
    img = Image.new('RGB', (600, 350), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Dialog title
    draw.rectangle([0, 0, 600, 35], fill=HEADER_BG)
    draw.text((10, 10), "Empty Bucket - WARNING", fill=(255, 165, 0))
    
    # Warning content
    y = 60
    draw.text((50, y), "⚠️ DANGER", fill=(255, 0, 0))
    draw.text((50, y+30), "This will permanently delete ALL objects in:", fill=TEXT_COLOR)
    draw.text((50, y+60), "my-awesome-bucket", fill=ACCENT_COLOR)
    
    draw.text((50, y+100), "This action CANNOT be undone!", fill=(255, 0, 0))
    
    draw.text((50, y+140), "Type the bucket name to confirm:", fill=TEXT_COLOR)
    draw.rectangle([50, y+170, 550, y+195], fill=INPUT_BG, outline=ACCENT_COLOR)
    draw.text((55, y+175), "my-awesome-bucket", fill=TEXT_COLOR)
    
    # Buttons
    y = 290
    draw.rectangle([350, y, 440, y+30], fill=BUTTON_BG, outline=ACCENT_COLOR)
    draw.text((375, y+8), "Cancel", fill=TEXT_COLOR)
    
    draw.rectangle([450, y, 570, y+30], fill=(180, 0, 0), outline=(200, 0, 0))
    draw.text((460, y+8), "Empty Bucket", fill=TEXT_COLOR)
    
    img.save(os.path.join(OUTPUT_DIR, "06-empty-bucket.png"))
    print("Created: 06-empty-bucket.png")

def create_bucket_browser():
    """Create a detailed bucket browser view."""
    img = Image.new('RGB', (1200, 800), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Title bar
    draw.rectangle([0, 0, 1200, 30], fill=HEADER_BG)
    draw.text((10, 8), "lolrus v0.1.0 - I has a bucket!", fill=TEXT_COLOR)
    
    # Toolbar
    y = 40
    draw.text((10, y), "Connection:", fill=TEXT_COLOR)
    draw.rectangle([100, y-2, 300, y+20], fill=INPUT_BG, outline=ACCENT_COLOR)
    draw.text((105, y), "Production Storage", fill=TEXT_COLOR)
    
    y = 75
    draw.text((10, y), "Bucket:", fill=TEXT_COLOR)
    draw.rectangle([100, y-2, 300, y+20], fill=INPUT_BG, outline=ACCENT_COLOR)
    draw.text((105, y), "website-assets", fill=TEXT_COLOR)
    
    y = 110
    draw.text((10, y), "Path:", fill=TEXT_COLOR)
    draw.rectangle([100, y-2, 600, y+20], fill=INPUT_BG, outline=ACCENT_COLOR)
    draw.text((105, y), "/images/products/", fill=TEXT_COLOR)
    
    # Buttons
    y = 145
    buttons = [("⬆️ Upload", ACCENT_COLOR), ("⬇️ Download", ACCENT_COLOR), 
               ("🗑️ Delete", (180, 0, 0)), ("🔄 Refresh", BUTTON_BG)]
    x = 10
    for text, color in buttons:
        width = len(text) * 8 + 15
        draw.rectangle([x, y, x+width, y+25], fill=color, outline=ACCENT_COLOR)
        draw.text((x+5, y+5), text, fill=TEXT_COLOR)
        x += width + 10
    
    # Table
    y = 185
    draw.rectangle([10, y, 1190, y+25], fill=HEADER_BG)
    headers = [("☐", 15), ("Name", 50), ("Size", 500), ("Last Modified", 650), ("Storage Class", 900)]
    for text, x_pos in headers:
        draw.text((x_pos, y+5), text, fill=TEXT_COLOR)
    
    # Table data
    y = 215
    items = [
        ("📁", ".. (parent)", "", "", ""),
        ("📁", "thumbnails/", "", "", ""),
        ("☑️", "hero-banner.jpg", "2.4 MB", "2024-01-15 14:30:22", "STANDARD"),
        ("☐", "logo-dark.png", "48 KB", "2024-01-15 14:28:10", "STANDARD"),
        ("☑️", "logo-light.png", "52 KB", "2024-01-15 14:28:10", "STANDARD"),
        ("☐", "product-001.jpg", "1.8 MB", "2024-01-14 09:15:33", "STANDARD"),
        ("☑️", "product-002.jpg", "1.9 MB", "2024-01-14 09:15:33", "STANDARD"),
        ("☐", "product-003.jpg", "2.1 MB", "2024-01-14 09:15:33", "STANDARD"),
        ("☐", "background.jpg", "3.2 MB", "2024-01-13 16:42:18", "STANDARD"),
    ]
    
    for i, (icon, name, size, modified, storage) in enumerate(items):
        bg = TABLE_ALT_ROW if i % 2 else BG_COLOR
        draw.rectangle([10, y, 1190, y+25], fill=bg)
        draw.text((15, y+5), icon, fill=TEXT_COLOR)
        draw.text((50, y+5), name, fill=TEXT_COLOR)
        draw.text((500, y+5), size, fill=TEXT_COLOR)
        draw.text((650, y+5), modified, fill=TEXT_COLOR)
        draw.text((900, y+5), storage, fill=TEXT_COLOR)
        y += 25
    
    # Status bar
    draw.rectangle([0, 770, 1200, 800], fill=HEADER_BG)
    draw.text((10, 778), "Ready | 3 of 6 objects selected | Total: 9.4 MB", fill=TEXT_COLOR)
    
    img.save(os.path.join(OUTPUT_DIR, "03-bucket-browser.png"))
    print("Created: 03-bucket-browser.png")

if __name__ == "__main__":
    print("Creating mockup screenshots...")
    print(f"Output directory: {OUTPUT_DIR}")
    
    create_main_window()
    create_connection_dialog()
    create_bucket_browser()
    create_upload_progress()
    create_delete_confirm()
    create_empty_bucket_dialog()
    
    print("\nDone! Mockup screenshots created.")
    print("\nNote: These are placeholder mockups. Replace with actual screenshots")
    print("by running the application and capturing the real UI.")
