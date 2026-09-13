import os
import shutil
import torch
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances

def cluster_images(embeddings_file, input_dir, output_dir, threshold=0.15, duplicate_threshold=0.01):
    if not os.path.exists(embeddings_file):
        print(f"Error: {embeddings_file} not found.")
        return

    print("Loading embeddings...")
    embeddings_dict = torch.load(embeddings_file, weights_only=False)
    
    # 1. Duplicate Removal
    filenames = list(embeddings_dict.keys())
    if not filenames:
        return
    
    embeddings = np.array([embeddings_dict[f] for f in filenames])
    
    # Compute pairwise cosine distances
    dist_matrix = cosine_distances(embeddings)
    
    duplicates_to_remove = set()
    for i in range(len(filenames)):
        if i in duplicates_to_remove:
            continue
        for j in range(i + 1, len(filenames)):
            if dist_matrix[i, j] < duplicate_threshold:
                duplicates_to_remove.add(j)
                print(f"Removed exact duplicate: {filenames[j]} (duplicate of {filenames[i]})")
                
    unique_indices = [i for i in range(len(filenames)) if i not in duplicates_to_remove]
    unique_filenames = [filenames[i] for i in unique_indices]
    unique_embeddings = embeddings[unique_indices]
    
    print(f"Removed {len(duplicates_to_remove)} duplicates. Clustering {len(unique_filenames)} unique images...")
    
    # 2. Agglomerative Clustering
    unique_dist_matrix = cosine_distances(unique_embeddings)
    clustering = AgglomerativeClustering(
        n_clusters=None, 
        metric='precomputed', 
        linkage='average', 
        distance_threshold=threshold
    )
    labels = clustering.fit_predict(unique_dist_matrix)
    
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    clusters = {}
    for filename, label in zip(unique_filenames, labels):
        clusters.setdefault(label, []).append(filename)
        
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

    parser = argparse.ArgumentParser(description="Cluster images using ResNet embeddings.")
    parser.add_argument("--embeddings", type=str, default=default_embeddings, help="Path to embeddings .pt file")
    parser.add_argument("--input-dir", type=str, default=default_input, help="Path to raw images directory")
    parser.add_argument("--output-dir", type=str, default=default_output, help="Path to output clusters directory")
    parser.add_argument("--threshold", type=float, default=0.15, help="Clustering distance threshold")
    parser.add_argument("--dup-threshold", type=float, default=0.01, help="Duplicate removal distance threshold")
    args = parser.parse_args()

    cluster_images(args.embeddings, args.input_dir, args.output_dir, threshold=args.threshold, duplicate_threshold=args.dup_threshold)
    print(f"Done. Check the '{args.output_dir}' folder.")
