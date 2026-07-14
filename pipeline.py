import os
import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances
import easyocr
from rembg import remove
import shutil

# Global models (loaded lazily to save startup time if needed, but here we load on first use)
resnet_model = None
efficientnet_model = None
preprocess = None
ocr_reader = None

def init_models():
    global resnet_model, efficientnet_model, preprocess, ocr_reader
    
    device = 'cpu'
    if torch.cuda.is_available():
        device = 'cuda'
    elif torch.backends.mps.is_available():
        device = 'mps'

    if resnet_model is None:
        weights = models.ResNet50_Weights.DEFAULT
        resnet_model = models.resnet50(weights=weights)
        resnet_model = torch.nn.Sequential(*(list(resnet_model.children())[:-1]))
        resnet_model.eval()
        resnet_model.to(device)
        
    if efficientnet_model is None:
        weights = models.EfficientNet_B0_Weights.DEFAULT
        efficientnet_model = models.efficientnet_b0(weights=weights)
        efficientnet_model = torch.nn.Sequential(
            efficientnet_model.features,
            efficientnet_model.avgpool,
            torch.nn.Flatten()
        )
        efficientnet_model.eval()
        efficientnet_model.to(device)

    if preprocess is None:
        preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    
    if ocr_reader is None:
        gpu = torch.cuda.is_available() or torch.backends.mps.is_available()
        ocr_reader = easyocr.Reader(['en'], gpu=gpu)

def run_ml_pipeline(temp_dir, image_files, update_progress):
    init_models()
    
    # 1. Feature Extraction
    update_progress("Extracting features from uploaded images...")
    embeddings_dict = {}
    
    device = 'cpu'
    if torch.cuda.is_available():
        device = 'cuda'
    elif torch.backends.mps.is_available():
        device = 'mps'
    
    for idx, filename in enumerate(image_files):
        update_progress(f"Extracting features... ({idx+1}/{len(image_files)})")
        file_path = os.path.join(temp_dir, filename)
        try:
            input_image = Image.open(file_path).convert('RGB')
            input_tensor = preprocess(input_image)
            input_batch = input_tensor.unsqueeze(0).to(device)

            with torch.no_grad():
                # Extract ResNet50 features
                resnet_output = resnet_model(input_batch)
                resnet_embed = resnet_output.squeeze().cpu().numpy()
                resnet_embed = resnet_embed / np.linalg.norm(resnet_embed) # Normalize
                
                # Extract EfficientNet_B0 features
                eff_output = efficientnet_model(input_batch)
                eff_embed = eff_output.squeeze().cpu().numpy()
                eff_embed = eff_embed / np.linalg.norm(eff_embed) # Normalize
            
            # Concatenate embeddings
            embedding_vector = np.concatenate([resnet_embed, eff_embed])
            embeddings_dict[filename] = embedding_vector
        except Exception as e:
            print(f"Error extracting features for {filename}: {e}")

    # 2. Duplicate Removal
    update_progress("Removing exact duplicates...")
    filenames = list(embeddings_dict.keys())
    if not filenames:
        return
        
    embedding_matrix = np.array([embeddings_dict[f] for f in filenames])
    distances = cosine_distances(embedding_matrix)
    
    duplicate_threshold = 0.01
    to_keep_indices = []
    
    for i in range(len(filenames)):
        is_duplicate = False
        for kept_idx in to_keep_indices:
            if distances[i, kept_idx] < duplicate_threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            to_keep_indices.append(i)

    unique_filenames = [filenames[i] for i in to_keep_indices]
    unique_distances = distances[np.ix_(to_keep_indices, to_keep_indices)]
    
    # 3. Clustering
    update_progress("Grouping similar products...")
    
    clusters_dict = {}
    if len(unique_filenames) > 1:
        clustering = AgglomerativeClustering(
            n_clusters=None, 
            metric='precomputed',
            linkage='average',
            distance_threshold=0.15
        )
        labels = clustering.fit_predict(unique_distances)
        for filename, label in zip(unique_filenames, labels):
            clusters_dict.setdefault(label, []).append(filename)
    elif len(unique_filenames) == 1:
        clusters_dict[0] = [unique_filenames[0]]

    # 4. OCR and Background Removal per Group
    
    for cluster_id, files in clusters_dict.items():
        update_progress(f"Processing Group {cluster_id + 1}/{len(clusters_dict)} (OCR & BG Removal)...")
        
        # OCR
        group_name = "unidentified"
        max_area = 0
        for img_name in files:
            img_path = os.path.join(temp_dir, img_name)
            try:
                results = ocr_reader.readtext(img_path)
                for (bbox, text, prob) in results:
                    width = abs(bbox[1][0] - bbox[0][0])
                    height = abs(bbox[2][1] - bbox[1][1])
                    area = width * height
                    if area > max_area and len(text) > 2:
                        clean_name = "".join(c for c in text if c.isalnum() or c in (' ', '_')).strip()
                        clean_name = clean_name.replace(" ", "_")
                        if clean_name:
                            max_area = area
                            group_name = clean_name
            except Exception as e:
                print(f"OCR Error on {img_name}: {e}")
        
        # BG Removal
        processed_images = []
        for idx, img_name in enumerate(files):
            input_path = os.path.join(temp_dir, img_name)
            bg_removed_name = f"bgrm_{img_name.rsplit('.', 1)[0]}.png"
            output_path = os.path.join(temp_dir, bg_removed_name)
            
            try:
                input_image = Image.open(input_path)
                output_image = remove(input_image)
                output_image.save(output_path)
                
                processed_images.append({
                    "original": img_name,
                    "bg_removed": bg_removed_name
                })
            except Exception as e:
                print(f"BG Removal Error on {img_name}: {e}")
                
        # Yield the completed group
        yield {
            "id": f"group_{cluster_id}",
            "name": group_name,
            "images": processed_images
        }
