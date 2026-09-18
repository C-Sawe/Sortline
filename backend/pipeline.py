import os
from PIL import Image
import numpy as np
from sklearn.cluster import HDBSCAN
from sklearn.metrics.pairwise import cosine_distances
import easyocr
from rembg import remove

from common import (
    get_device,
    load_clip_model,
    embed_image_clip,
    get_rembg_session,
    compute_phash,
    clean_ocr_name,
    group_by_ocr_name,
)

# Global models (loaded lazily to save startup time if needed, but here we load on first use)
clip_model = None
clip_processor = None
ocr_reader = None
device = "cpu"

def init_models():
    global clip_model, clip_processor, ocr_reader, device

    device = get_device()

    if clip_model is None:
        clip_model, clip_processor = load_clip_model(device)

    if ocr_reader is None:
        gpu = device in ("cuda", "mps")
        ocr_reader = easyocr.Reader(['en'], gpu=gpu)

    # Warm the rembg session too so the first group doesn't pay the load cost.
    get_rembg_session()

def run_ml_pipeline(temp_dir, image_files, update_progress):
    init_models()

    # 1. Feature Extraction (CLIP embeddings - much better than ImageNet-classification
    # features at recognizing "same product, different angle/lighting")
    update_progress("Extracting features from uploaded images...")
    embeddings_dict = {}
    hashes_dict = {}

    for idx, filename in enumerate(image_files):
        update_progress(f"Extracting features... ({idx+1}/{len(image_files)})")
        file_path = os.path.join(temp_dir, filename)
        try:
            input_image = Image.open(file_path).convert('RGB')
            embeddings_dict[filename] = embed_image_clip(input_image, clip_model, clip_processor, device)
            hashes_dict[filename] = compute_phash(input_image)
        except Exception as e:
            print(f"Error extracting features for {filename}: {e}")

    # 2. Duplicate Removal - perceptual hash on the actual pixels, since embedding
    # distance is a semantic signal (good for clustering) and can call two similar-
    # but-different products "duplicates" too.
    update_progress("Removing exact duplicates...")
    filenames = list(embeddings_dict.keys())
    if not filenames:
        return

    duplicate_hash_threshold = 10  # Hamming distance out of 256 bits
    to_keep_indices = []

    for i in range(len(filenames)):
        is_duplicate = False
        for kept_idx in to_keep_indices:
            if hashes_dict[filenames[i]] - hashes_dict[filenames[kept_idx]] <= duplicate_hash_threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            to_keep_indices.append(i)

    unique_filenames = [filenames[i] for i in to_keep_indices]

    # 3. Clustering (semantic grouping of look-alike products)
    update_progress("Grouping similar products...")

    clusters_dict = {}
    if len(unique_filenames) > 1:
        embedding_matrix = np.array([embeddings_dict[f] for f in unique_filenames])
        unique_distances = cosine_distances(embedding_matrix)

        # HDBSCAN infers cluster count/shape from density instead of a hand-tuned
        # fixed distance cutoff, and correctly leaves genuine one-offs ungrouped.
        clustering = HDBSCAN(
            min_cluster_size=2,
            metric='precomputed',
            copy=False,
        )
        labels = clustering.fit_predict(unique_distances)

        next_singleton_label = (labels.max() + 1) if len(labels) else 0
        resolved_labels = []
        for label in labels:
            if label == -1:
                resolved_labels.append(next_singleton_label)
                next_singleton_label += 1
            else:
                resolved_labels.append(label)

        for filename, label in zip(unique_filenames, resolved_labels):
            clusters_dict.setdefault(label, []).append(filename)
    elif len(unique_filenames) == 1:
        clusters_dict[0] = [unique_filenames[0]]

    # 4. OCR, cluster splitting, and Background Removal per Group
    rembg_session = get_rembg_session()

    for cluster_id, files in clusters_dict.items():
        update_progress(f"Processing Group {cluster_id + 1}/{len(clusters_dict)} (OCR & BG Removal)...")

        # OCR - read every image individually (not just the group's best hit) so a
        # visually-similar cluster that actually contains multiple distinct products
        # (same bottle/pack, different label) can be split apart below.
        per_image_names = []
        for img_name in files:
            img_path = os.path.join(temp_dir, img_name)
            try:
                results = ocr_reader.readtext(img_path)
                name, area = clean_ocr_name(results)
            except Exception as e:
                print(f"OCR Error on {img_name}: {e}")
                name, area = "unidentified", 0
            per_image_names.append((img_name, name, area))

        subgroups = group_by_ocr_name(per_image_names)

        for sub_idx, (group_name, sub_files) in enumerate(subgroups):
            # BG Removal
            processed_images = []
            for img_name in sub_files:
                input_path = os.path.join(temp_dir, img_name)
                bg_removed_name = f"bgrm_{img_name.rsplit('.', 1)[0]}.png"
                output_path = os.path.join(temp_dir, bg_removed_name)

                try:
                    input_image = Image.open(input_path)
                    output_image = remove(input_image, session=rembg_session)
                    output_image.save(output_path)

                    processed_images.append({
                        "original": img_name,
                        "bg_removed": bg_removed_name
                    })
                except Exception as e:
                    print(f"BG Removal Error on {img_name}: {e}")

            group_id = f"group_{cluster_id}" if len(subgroups) == 1 else f"group_{cluster_id}_{sub_idx}"

            # Yield the completed group
            yield {
                "id": group_id,
                "name": group_name,
                "images": processed_images
            }
