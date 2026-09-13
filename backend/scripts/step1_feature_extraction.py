import os
import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image

def get_image_embeddings(image_dir):
    # Load pre-trained ResNet50 model
    # We remove the final classification layer to get the feature embeddings instead
    weights = models.ResNet50_Weights.DEFAULT
    model = models.resnet50(weights=weights)
    model = torch.nn.Sequential(*(list(model.children())[:-1]))
    model.eval() # Set to evaluation mode

    # Standard preprocessing for ResNet
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    embeddings = {}
    
    print("Extracting features from images...")
    for filename in sorted(os.listdir(image_dir)):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            file_path = os.path.join(image_dir, filename)
            
            try:
                # Load and preprocess image
                input_image = Image.open(file_path).convert('RGB')
                input_tensor = preprocess(input_image)
                input_batch = input_tensor.unsqueeze(0) # create a mini-batch as expected by the model

                # Move the input and model to GPU/MPS for speed if available
                device = 'cpu'
                if torch.cuda.is_available():
                    device = 'cuda'
                elif torch.backends.mps.is_available():
                    device = 'mps'

                input_batch = input_batch.to(device)
                model.to(device)

                with torch.no_grad():
                    output = model(input_batch)
                
                # The output has shape [1, 2048, 1, 1], we flatten it to [2048]
                embedding_vector = output.squeeze().cpu().numpy()
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

    parser = argparse.ArgumentParser(description="Extract ResNet50 embeddings from images.")
    parser.add_argument("--input-dir", type=str, default=default_input, help="Path to images directory")
    parser.add_argument("--output", type=str, default=default_output, help="Path to output .pt file")
    args = parser.parse_args()

    if not os.path.exists(args.input_dir):
        print(f"Error: {args.input_dir} not found.")
    else:
        embeddings = get_image_embeddings(args.input_dir)
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        torch.save(embeddings, args.output)
        print(f"Saved {len(embeddings)} embeddings to {args.output}.")
