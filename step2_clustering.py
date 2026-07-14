import os
import shutil
import torch
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances

def cluster_images(embeddings_file, output_dir, threshold=0.15, duplicate_threshold=0.01):
    if not os.path.exists(embeddings_file):
        print(f"Error: {embeddings_file} not found.")
        return

    embeddings_dict = torch.load(embeddings_file, weights_only=False)
    
    filenames = list(embeddings_dict.keys())
    # Convert list of 1D arrays into a 2D numpy array
    embedding_matrix = np.array([embeddings_dict[f] for f in filenames])

    print(f"Loaded {len(filenames)} embeddings. Checking for duplicates...")
    
    # Calculate cosine distance matrix (1 - cosine similarity)
    distances = cosine_distances(embedding_matrix)
    
    # Identify duplicates (distance < duplicate_threshold)
    to_keep_indices = []
    duplicates_found = 0
    
    for i in range(len(filenames)):
        is_duplicate = False
        # Check if this image is a duplicate of any image we've already decided to keep
        for kept_idx in to_keep_indices:
            if distances[i, kept_idx] < duplicate_threshold:
                is_duplicate = True
                duplicates_found += 1
                print(f"Removed exact duplicate: {filenames[i]} (duplicate of {filenames[kept_idx]})")
                break
        
        if not is_duplicate:
            to_keep_indices.append(i)
            
    print(f"Removed {duplicates_found} duplicates. Clustering {len(to_keep_indices)} unique images...")

    # Filter filenames and distance matrix for unique images
    unique_filenames = [filenames[i] for i in to_keep_indices]
    unique_distances = distances[np.ix_(to_keep_indices, to_keep_indices)]
    
    # Use Agglomerative Clustering
    clustering = AgglomerativeClustering(
        n_clusters=None, 
        metric='precomputed',
        linkage='average',
        distance_threshold=threshold
    )
    
    labels = clustering.fit_predict(unique_distances)
    
    # Create output directories and copy files
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
            src = os.path.join("mosop_images", f)
            dst = os.path.join(cluster_folder, f)
            shutil.copy2(src, dst)

if __name__ == "__main__":
    cluster_images('embeddings.pt', 'mosop_clusters', threshold=0.15, duplicate_threshold=0.01)
    print("Done. Check the 'mosop_clusters' folder.")
