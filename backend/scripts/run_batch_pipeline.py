import os
import shutil
import argparse
import time

from step1_feature_extraction import get_image_embeddings
from step2_clustering import cluster_images
from step3_process import process_clusters
from step5_optimize_web import optimize_for_web
import torch

def run_batch(input_folder_name, merge_to_master=True):
    t_start = time.time()
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data_dir = os.path.join(BASE_DIR, "data")
    
    input_dir = os.path.join(data_dir, input_folder_name)
    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} not found!")
        return

    # Derive clean prefix for output folders
    clean_prefix = input_folder_name.lower().replace(" ", "_")
    
    embeddings_file = os.path.join(data_dir, f"embeddings_{clean_prefix}.pt")
    clusters_dir = os.path.join(data_dir, f"{clean_prefix}_clusters")
    final_products_dir = os.path.join(data_dir, f"{clean_prefix}_final_products")
    optimized_web_dir = os.path.join(data_dir, f"{clean_prefix}_optimized_web")
    
    master_final_dir = os.path.join(data_dir, "mosop_final_products")
    master_opt_dir = os.path.join(data_dir, "mosop_optimized_web")

    print("=" * 60)
    print(f"SORTLINE BATCH PIPELINE")
    print(f"Input Directory:       {input_dir}")
    print(f"Embeddings File:       {embeddings_file}")
    print(f"Clusters Directory:    {clusters_dir}")
    print(f"Final Products (PNG):  {final_products_dir}")
    print(f"Web Optimized (WebP):  {optimized_web_dir}")
    print("=" * 60)

    # 1. Feature Extraction
    print("\n>>> STEP 1: Feature Extraction (ResNet50)")
    embeddings = get_image_embeddings(input_dir)
    torch.save(embeddings, embeddings_file)
    print(f"Extracted and saved {len(embeddings)} embeddings to {embeddings_file}")

    # 2. Clustering & Duplicate Detection
    print("\n>>> STEP 2: Clustering & Duplicate Removal")
    cluster_images(embeddings_file, input_dir, clusters_dir, threshold=0.15, duplicate_threshold=0.01)

    # 3. OCR Naming & Rembg Background Removal
    print("\n>>> STEP 3: OCR Naming & AI Background Removal")
    process_clusters(clusters_dir, final_products_dir, clean=True)

    # 4. Web Optimization (800px WebP)
    print("\n>>> STEP 4: Web Optimization (800px WebP)")
    optimize_for_web(final_products_dir, optimized_web_dir, target_width=800, quality=85)

    # 5. Non-destructive Master Catalog Merge
    if merge_to_master:
        print("\n>>> STEP 5: Consolidating into Master Catalog")
        os.makedirs(master_final_dir, exist_ok=True)
        os.makedirs(master_opt_dir, exist_ok=True)

        merged_count = 0
        for png_file in sorted(os.listdir(final_products_dir)):
            if not png_file.endswith('.png'):
                continue
            src_png = os.path.join(final_products_dir, png_file)
            dst_png = os.path.join(master_final_dir, png_file)
            
            # Resolve collision if necessary
            name_stem, ext = os.path.splitext(png_file)
            counter = 1
            final_name_stem = name_stem
            while os.path.exists(dst_png):
                final_name_stem = f"{name_stem}_import_{counter}"
                dst_png = os.path.join(master_final_dir, f"{final_name_stem}.png")
                counter += 1
            
            shutil.copy2(src_png, dst_png)
            
            # Also copy corresponding webp if present
            webp_file = f"{name_stem}.webp"
            src_webp = os.path.join(optimized_web_dir, webp_file)
            if os.path.exists(src_webp):
                dst_webp = os.path.join(master_opt_dir, f"{final_name_stem}.webp")
                shutil.copy2(src_webp, dst_webp)

            merged_count += 1

        print(f"Merged {merged_count} new product images into master catalogs:")
        print(f"  -> {master_final_dir} (Total: {len(os.listdir(master_final_dir))} items)")
        print(f"  -> {master_opt_dir} (Total: {len(os.listdir(master_opt_dir))} items)")

    elapsed = time.time() - t_start
    print("\n" + "=" * 60)
    print(f"SORTLINE PIPELINE COMPLETED IN {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run complete Sortline pipeline on a folder in data/")
    parser.add_argument("--folder", type=str, default="Mosop Imports 1", help="Folder name inside data/")
    parser.add_argument("--no-merge", action="store_true", help="Do not merge results into master folders")
    args = parser.parse_args()

    run_batch(args.folder, merge_to_master=not args.no_merge)
