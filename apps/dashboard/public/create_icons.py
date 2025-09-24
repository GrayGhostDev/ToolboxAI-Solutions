#!/usr/bin/env python3
"""Generate placeholder icons for the manifest."""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size):
    """Create a simple icon with gradient background and text."""
    # Create image with gradient background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Create gradient effect (purple to blue)
    for i in range(size):
        # Interpolate between colors
        r = int(102 + (118 - 102) * (i / size))  # From #667eea to #764ba2
        g = int(126 + (75 - 126) * (i / size))
        b = int(234 + (162 - 234) * (i / size))
        draw.rectangle([(0, i), (size, i+1)], fill=(r, g, b, 255))

    # Add rounded corners
    corner_radius = int(size * 0.15)
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (size, size)], radius=corner_radius, fill=255)

    # Apply mask for rounded corners
    output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0))
    output.putalpha(mask)

    # Add text "TB"
    draw = ImageDraw.Draw(output)
    try:
        # Try to use a nice font, fallback to default if not available
        font_size = int(size * 0.4)
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        # Use default font if system font not found
        font = ImageFont.load_default()

    text = "TB"
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center the text
    position = ((size - text_width) / 2, (size - text_height) / 2)
    draw.text(position, text, fill='white', font=font)

    return output

# Create both icon sizes
icon_192 = create_icon(192)
icon_512 = create_icon(512)

# Save the icons
script_dir = os.path.dirname(os.path.abspath(__file__))
icon_192.save(os.path.join(script_dir, 'icon-192x192.png'))
icon_512.save(os.path.join(script_dir, 'icon-512x512.png'))

print("Icons created successfully:")
print("- icon-192x192.png")
print("- icon-512x512.png")