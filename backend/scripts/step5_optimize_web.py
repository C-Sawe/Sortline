import os
import argparse
from PIL import Image

def optimize_for_web(input_dir, output_dir, target_width=800, quality=85):
    if not os.path.exists(input_dir):
        print(f"Error: {input_dir} not found.")
        return

    os.makedirs(output_dir, exist_ok=True)
    images = sorted([f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
    print(f"Optimizing {len(images)} images from {input_dir} -> {output_dir} (target width: {target_width}px, WebP quality: {quality})...")

    count = 0
    for filename in images:
        input_path = os.path.join(input_dir, filename)
        base_name = os.path.splitext(filename)[0]
        output_filename = f"{base_name}.webp"
        output_path = os.path.join(output_dir, output_filename)

        try:
            with Image.open(input_path) as img:
                # Convert to RGBA if not already
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                # Calculate proportional height for target width
                orig_w, orig_h = img.size
                if orig_w > target_width:
                    target_height = int(orig_h * (target_width / orig_w))
                    resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                else:
                    resized_img = img

                resized_img.save(output_path, "WEBP", quality=quality)
                count += 1
                print(f"  Optimized: {filename} ({orig_w}x{orig_h}) -> {output_filename} ({resized_img.size[0]}x{resized_img.size[1]})")
        except Exception as e:
            print(f"  Error optimizing {filename}: {e}")

    print(f"Successfully optimized {count}/{len(images)} images to WebP.")

if __name__ == "__main__":
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    default_input = os.path.join(BASE_DIR, "data", "mosop_final_products")
    default_output = os.path.join(BASE_DIR, "data", "mosop_optimized_web")

    parser = argparse.ArgumentParser(description="Convert and resize catalog images to web-optimized WebP format.")
    parser.add_argument("--input-dir", type=str, default=default_input, help="Input directory containing PNG images")
    parser.add_argument("--output-dir", type=str, default=default_output, help="Output directory for WebP images")
    parser.add_argument("--width", type=int, default=800, help="Target image width in pixels (default 800)")
    parser.add_argument("--quality", type=int, default=85, help="WebP quality (default 85)")
    args = parser.parse_args()

    optimize_for_web(args.input_dir, args.output_dir, target_width=args.width, quality=args.quality)
