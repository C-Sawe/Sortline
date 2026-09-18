import os
import sys
import shutil
import torch
import numpy as np
from PIL import Image
from sklearn.cluster import HDBSCAN
from sklearn.metrics.pairwise import cosine_distances

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import compute_phash


def cluster_images(embeddings_file, input_dir, output_dir, min_cluster_size=2, duplicate_hash_threshold=10):
    if not os.path.exists(embeddings_file):
        print(f"Error: {embeddings_file} not found.")
        return

    print("Loading embeddings...")
    embeddings_dict = torch.load(embeddings_file, weights_only=False)

    filenames = list(embeddings_dict.keys())
    if not filenames:
        return

    # 1. Duplicate Removal - perceptual hash on pixels catches true near-duplicate
    # shots (same frame, minor recompression/crop) more precisely than embedding
    # distance, which is a semantic signal meant for clustering look-alikes.
    print("Hashing images for duplicate detection...")
    hashes = {}
    for f in filenames:
        with Image.open(os.path.join(input_dir, f)) as img:
            hashes[f] = compute_phash(img)

    duplicates_to_remove = set()
    for i in range(len(filenames)):
        if i in duplicates_to_remove:
            continue
        for j in range(i + 1, len(filenames)):
            if hashes[filenames[i]] - hashes[filenames[j]] <= duplicate_hash_threshold:
                duplicates_to_remove.add(j)
                print(f"Removed exact duplicate: {filenames[j]} (duplicate of {filenames[i]})")

    unique_indices = [i for i in range(len(filenames)) if i not in duplicates_to_remove]
    unique_filenames = [filenames[i] for i in unique_indices]
    unique_embeddings = np.array([embeddings_dict[f] for f in unique_filenames])

    print(f"Removed {len(duplicates_to_remove)} duplicates. Clustering {len(unique_filenames)} unique images...")

    # 2. Clustering - HDBSCAN infers cluster count/shape from embedding density
    # instead of a hand-tuned fixed distance cutoff, and correctly leaves genuine
    # one-off photos ungrouped instead of forcing them into the nearest cluster.
    clusters = {}
    if len(unique_filenames) > 1:
        unique_dist_matrix = cosine_distances(unique_embeddings)
        clustering = HDBSCAN(min_cluster_size=min_cluster_size, metric='precomputed', copy=False)
        labels = clustering.fit_predict(unique_dist_matrix)

        next_singleton_label = (labels.max() + 1) if len(labels) else 0
        resolved_labels = []
        for label in labels:
            if label == -1:
                resolved_labels.append(next_singleton_label)
                next_singleton_label += 1
            else:
                resolved_labels.append(label)

        for filename, label in zip(unique_filenames, resolved_labels):
            clusters.setdefault(label, []).append(filename)
    elif len(unique_filenames) == 1:
        clusters[0] = [unique_filenames[0]]

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Found {len(clusters)} clusters.")

    for label, files in clusters.items():
        cluster_folder = os.path.join(output_dir, f"group_{label}")
        os.makedirs(cluster_folder, exist_ok=True)

        for f in files:
            src = os.path.join(input_dir, f)
            dst = os.path.join(cluster_folder, f)
            shutil.copy2(src, dst)

if __name__ == "__main__":
    import os
    import argparse

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    default_embeddings = os.path.join(BASE_DIR, 'embeddings.pt')
    default_input = os.path.join(BASE_DIR, 'data', 'Mosop_Products')
    default_output = os.path.join(BASE_DIR, 'data', 'mosop_clusters')

    parser = argparse.ArgumentParser(description="Cluster images using CLIP embeddings.")
    parser.add_argument("--embeddings", type=str, default=default_embeddings, help="Path to embeddings .pt file")
    parser.add_argument("--input-dir", type=str, default=default_input, help="Path to raw images directory")
    parser.add_argument("--output-dir", type=str, default=default_output, help="Path to output clusters directory")
    parser.add_argument("--min-cluster-size", type=int, default=2, help="HDBSCAN minimum cluster size")
    parser.add_argument("--dup-hash-threshold", type=int, default=10, help="Perceptual hash Hamming distance below which two images count as duplicates")
    args = parser.parse_args()

    cluster_images(args.embeddings, args.input_dir, args.output_dir, min_cluster_size=args.min_cluster_size, duplicate_hash_threshold=args.dup_hash_threshold)
    print(f"Done. Check the '{args.output_dir}' folder.")
