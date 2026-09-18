import os
import sys
import easyocr
import shutil
from PIL import Image
from rembg import remove

import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import clean_ocr_name, get_rembg_session, group_by_ocr_name

def process_clusters(input_dir, output_dir, clean=False):
    if not os.path.exists(input_dir):
        print(f"Error: {input_dir} not found.")
        return

    if clean and os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    print("Loading OCR Model...")
    gpu_available = torch.cuda.is_available() or torch.backends.mps.is_available()
    reader = easyocr.Reader(['en'], gpu=gpu_available)
    rembg_session = get_rembg_session()

    print(f"Processing clusters from {input_dir}...")
    
    for group_folder in sorted(os.listdir(input_dir)):
        group_path = os.path.join(input_dir, group_folder)
        
        if os.path.isdir(group_path):
            images_in_group = sorted([f for f in os.listdir(group_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
            
            # 1. Identify Name(s) - read every image individually (not just the
            # group's best hit) so a visually-similar cluster that actually
            # contains multiple distinct products (same bottle/pack, different
            # label) can be split apart below.
            per_image_names = []
            for img in images_in_group:
                img_path = os.path.join(group_path, img)
                try:
                    results = reader.readtext(img_path)
                    name, area = clean_ocr_name(results)
                except Exception as e:
                    print(f"OCR Error on {img}: {e}")
                    name, area = "unidentified", 0
                per_image_names.append((img, name, area))

            subgroups = group_by_ocr_name(per_image_names)
            if len(subgroups) > 1:
                print(f"\nGroup {group_folder} split into {len(subgroups)} products: {[n for n, _ in subgroups]}")

            for group_name, sub_files in subgroups:
                print(f"\nGroup {group_folder} ({group_name}): {len(sub_files)} image(s)")

                # 2. Rename & Remove Background
                for idx, img in enumerate(sub_files):
                    input_path = os.path.join(group_path, img)
                    new_filename = f"{group_name}_{idx+1}.png"
                    output_path = os.path.join(output_dir, new_filename)

                    # Handle duplicate names if we end up with multiple 'unidentified' groups or existing files
                    counter = 1
                    while os.path.exists(output_path):
                        new_filename = f"{group_name}_{idx+1}_{counter}.png"
                        output_path = os.path.join(output_dir, new_filename)
                        counter += 1

                    try:
                        print(f"  Removing background for {img} -> {new_filename}")
                        input_image = Image.open(input_path)
                        output_image = remove(input_image, session=rembg_session)
                        output_image.save(output_path)
                    except Exception as e:
                        print(f"  Error processing {img}: {e}")

if __name__ == "__main__":
    import os
    import argparse

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    default_input = os.path.join(BASE_DIR, "data", "mosop_clusters")
    default_output = os.path.join(BASE_DIR, "data", "mosop_final_products")

    parser = argparse.ArgumentParser(description="OCR name identification and background removal on clustered images.")
    parser.add_argument("--input-dir", type=str, default=default_input, help="Path to clusters directory")
    parser.add_argument("--output-dir", type=str, default=default_output, help="Path to final products output directory")
    parser.add_argument("--clean", action="store_true", help="Remove existing output directory before processing")
    args = parser.parse_args()

    process_clusters(args.input_dir, args.output_dir, clean=args.clean)
    print(f"Done. Check the '{args.output_dir}' folder.")
