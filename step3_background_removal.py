import os
from PIL import Image
from rembg import remove

def remove_backgrounds(input_dir, output_dir):
    if not os.path.exists(input_dir):
        print(f"Error: {input_dir} not found.")
        return

    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Removing backgrounds from images in {input_dir}...")
    
    # Iterate through cluster folders
    for group_folder in os.listdir(input_dir):
        group_path = os.path.join(input_dir, group_folder)
        
        if os.path.isdir(group_path):
            output_group_path = os.path.join(output_dir, group_folder)
            os.makedirs(output_group_path, exist_ok=True)
            
            # Process each image in the group
            for filename in os.listdir(group_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    input_path = os.path.join(group_path, filename)
                    # Output as PNG to support transparency
                    output_filename = os.path.splitext(filename)[0] + '.png'
                    output_path = os.path.join(output_group_path, output_filename)
                    
                    try:
                        print(f"Processing {input_path} -> {output_path}")
                        input_image = Image.open(input_path)
                        output_image = remove(input_image)
                        output_image.save(output_path)
                    except Exception as e:
                        print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    input_directory = "mosop_clusters"
    output_directory = "mosop_bg_removed"
    remove_backgrounds(input_directory, output_directory)
    print("Done. Check the 'mosop_bg_removed' folder.")
