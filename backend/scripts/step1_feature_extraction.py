import os
import sys
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import get_device, load_clip_model, embed_image_clip


def get_image_embeddings(image_dir):
    device = get_device()
    model, processor = load_clip_model(device)

    embeddings = {}

    print(f"Extracting CLIP features from images (device: {device})...")
    for filename in sorted(os.listdir(image_dir)):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            file_path = os.path.join(image_dir, filename)

            try:
                input_image = Image.open(file_path).convert('RGB')
                embedding_vector = embed_image_clip(input_image, model, processor, device)
                embeddings[filename] = embedding_vector

                print(f"Processed {filename} -> Embedding shape: {embedding_vector.shape}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    return embeddings

if __name__ == "__main__":
    import os
    import argparse

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    default_input = os.path.join(BASE_DIR, "data", "Mosop_Products")
    default_output = os.path.join(BASE_DIR, "embeddings.pt")

    parser = argparse.ArgumentParser(description="Extract CLIP embeddings from images.")
    parser.add_argument("--input-dir", type=str, default=default_input, help="Path to images directory")
    parser.add_argument("--output", type=str, default=default_output, help="Path to output .pt file")
    args = parser.parse_args()

    if not os.path.exists(args.input_dir):
        print(f"Error: {args.input_dir} not found.")
    else:
        import torch
        embeddings = get_image_embeddings(args.input_dir)
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        torch.save(embeddings, args.output)
        print(f"Saved {len(embeddings)} embeddings to {args.output}.")
