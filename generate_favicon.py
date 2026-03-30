import os
import sys

try:
    import cairosvg
    from PIL import Image
    import io
except ImportError:
    print("Missing requirements! Please install them by running:")
    print("pip install cairosvg Pillow")
    sys.exit(1)

def convert_svg_to_ico(svg_path, ico_path):
    if not os.path.exists(svg_path):
        print(f"Error: Could not find {svg_path}")
        return

    print(f"Converting {svg_path} to PNG in memory...")
    try:
        # Convert SVG to PNG in memory
        png_data = cairosvg.svg2png(url=svg_path, output_width=256, output_height=256)

        # Load PNG with Pillow
        image = Image.open(io.BytesIO(png_data))

        # Save as ICO with multiple sizes suitable for favicons
        print(f"Saving to {ico_path}...")
        image.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])

        print("Success! Favicon generated.")
    except Exception as e:
        print(f"Failed to convert: {e}")
        print("Note: cairosvg requires OS-level Cairo libraries. On macOS, run: brew install cairo")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SVG_FILE = os.path.join(BASE_DIR, "static", "images", "logo.svg")
    ICO_FILE = os.path.join(BASE_DIR, "static", "images", "favicon.ico")

    convert_svg_to_ico(SVG_FILE, ICO_FILE)
