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
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    input_dir = os.path.join(BASE_DIR, 'data', 'Mosop_Products')
    output_dir = os.path.join(BASE_DIR, 'data', 'mosop_clusters')
    cluster_images('embeddings.pt', input_dir, output_dir, threshold=0.15, duplicate_threshold=0.01)
    print("Done. Check the 'mosop_clusters' folder.")
