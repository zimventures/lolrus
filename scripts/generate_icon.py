#!/usr/bin/env python3
"""
Generate the lolrus application icon.

Creates a cute walrus icon in multiple formats:
- PNG files at various sizes
- ICO file for Windows
- ICNS file for macOS (if running on macOS)
"""

from pathlib import Path

from PIL import Image, ImageDraw


def create_walrus_icon(size: int) -> Image.Image:
    """Create a walrus icon at the specified size."""
    # Create image with transparency
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Scale factor for drawing
    s = size / 256

    # Colors
    body_color = (139, 119, 101)  # Brownish-gray walrus color
    body_dark = (119, 99, 81)  # Darker shade
    tusk_color = (255, 250, 240)  # Ivory
    tusk_shadow = (220, 215, 205)
    nose_color = (80, 60, 50)  # Dark brown
    eye_color = (40, 30, 25)  # Nearly black
    whisker_color = (60, 50, 40)
    bucket_color = (70, 130, 180)  # Steel blue bucket
    bucket_dark = (50, 100, 150)
    bucket_highlight = (100, 160, 210)

    # Draw bucket behind walrus (bottom portion)
    bucket_top = int(160 * s)
    bucket_bottom = int(250 * s)
    bucket_left = int(50 * s)
    bucket_right = int(206 * s)

    # Bucket body (trapezoid shape approximated with polygon)
    bucket_points = [
        (int(60 * s), bucket_top),
        (int(196 * s), bucket_top),
        (int(206 * s), bucket_bottom),
        (int(50 * s), bucket_bottom),
    ]
    draw.polygon(bucket_points, fill=bucket_color)

    # Bucket rim
    draw.ellipse(
        [int(55 * s), int(150 * s), int(201 * s), int(175 * s)],
        fill=bucket_highlight,
        outline=bucket_dark,
        width=max(1, int(2 * s)),
    )

    # Bucket bands
    for y_offset in [60, 100]:
        y = int((160 + y_offset) * s)
        draw.line(
            [(int(52 * s), y), (int(204 * s), y)],
            fill=bucket_dark,
            width=max(1, int(3 * s)),
        )

    # Main walrus face (large circle)
    face_bbox = [int(28 * s), int(20 * s), int(228 * s), int(200 * s)]
    draw.ellipse(face_bbox, fill=body_color)

    # Snout/muzzle area (lighter, rounder)
    snout_bbox = [int(58 * s), int(90 * s), int(198 * s), int(190 * s)]
    draw.ellipse(snout_bbox, fill=body_dark)

    # Left tusk
    tusk_left_points = [
        (int(85 * s), int(140 * s)),
        (int(75 * s), int(145 * s)),
        (int(65 * s), int(210 * s)),
        (int(80 * s), int(205 * s)),
        (int(95 * s), int(145 * s)),
    ]
    draw.polygon(tusk_left_points, fill=tusk_color, outline=tusk_shadow)

    # Right tusk
    tusk_right_points = [
        (int(171 * s), int(140 * s)),
        (int(181 * s), int(145 * s)),
        (int(191 * s), int(210 * s)),
        (int(176 * s), int(205 * s)),
        (int(161 * s), int(145 * s)),
    ]
    draw.polygon(tusk_right_points, fill=tusk_color, outline=tusk_shadow)

    # Nose
    nose_bbox = [int(108 * s), int(110 * s), int(148 * s), int(145 * s)]
    draw.ellipse(nose_bbox, fill=nose_color)

    # Nostrils
    draw.ellipse(
        [int(115 * s), int(120 * s), int(125 * s), int(135 * s)],
        fill=(30, 20, 15),
    )
    draw.ellipse(
        [int(131 * s), int(120 * s), int(141 * s), int(135 * s)],
        fill=(30, 20, 15),
    )

    # Eyes
    eye_size = int(20 * s)
    # Left eye
    draw.ellipse(
        [int(70 * s), int(70 * s), int(70 * s) + eye_size, int(70 * s) + eye_size],
        fill=eye_color,
    )
    # Eye highlight
    draw.ellipse(
        [int(75 * s), int(73 * s), int(75 * s) + int(6 * s), int(73 * s) + int(6 * s)],
        fill=(255, 255, 255),
    )

    # Right eye
    draw.ellipse(
        [int(166 * s), int(70 * s), int(166 * s) + eye_size, int(70 * s) + eye_size],
        fill=eye_color,
    )
    # Eye highlight
    draw.ellipse(
        [int(171 * s), int(73 * s), int(171 * s) + int(6 * s), int(73 * s) + int(6 * s)],
        fill=(255, 255, 255),
    )

    # Whisker dots (on snout)
    whisker_y = int(150 * s)
    dot_size = max(2, int(6 * s))
    for x in [75, 90, 105]:
        draw.ellipse(
            [int(x * s), whisker_y, int(x * s) + dot_size, whisker_y + dot_size],
            fill=whisker_color,
        )
    for x in [151, 166, 181]:
        draw.ellipse(
            [int(x * s), whisker_y, int(x * s) + dot_size, whisker_y + dot_size],
            fill=whisker_color,
        )

    return img


def main():
    """Generate icon files."""
    # Output directory
    output_dir = Path(__file__).parent.parent / "assets"
    output_dir.mkdir(exist_ok=True)

    # Generate PNG at various sizes
    sizes = [16, 32, 48, 64, 128, 256, 512]
    images = {}

    for size in sizes:
        img = create_walrus_icon(size)
        img.save(output_dir / f"icon_{size}.png")
        images[size] = img
        print(f"Created icon_{size}.png")

    # Create ICO file for Windows (contains multiple sizes)
    # ICO format requires saving from largest to smallest, with proper format
    ico_sizes = [256, 128, 64, 48, 32, 16]
    ico_images = [images[s] for s in ico_sizes]

    # Save ICO with all sizes embedded
    ico_images[0].save(
        output_dir / "lolrus.ico",
        format="ICO",
        append_images=ico_images[1:],
    )
    print(f"Created lolrus.ico ({(output_dir / 'lolrus.ico').stat().st_size} bytes)")

    # Also save main icon as lolrus.png
    images[256].save(output_dir / "lolrus.png")
    print("Created lolrus.png")

    print(f"\nIcon files saved to: {output_dir}")


if __name__ == "__main__":
    main()
