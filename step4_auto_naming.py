import os
import easyocr
import shutil

def rename_images(input_dir, output_dir):
    if not os.path.exists(input_dir):
        print(f"Error: {input_dir} not found.")
        return

    os.makedirs(output_dir, exist_ok=True)
    
    print("Loading OCR Model...")
    # Initialize EasyOCR reader
    reader = easyocr.Reader(['en'], gpu=True) # Uses GPU if available
    
    print(f"Renaming images from {input_dir}...")
    
    for group_folder in os.listdir(input_dir):
        group_path = os.path.join(input_dir, group_folder)
        
        if os.path.isdir(group_path):
            images_in_group = [f for f in os.listdir(group_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            # Try to find a name from the first image in the group
            group_name = "Product"
            for img in images_in_group:
                img_path = os.path.join(group_path, img)
                try:
                    results = reader.readtext(img_path)
                    if results:
                        # Find the text with the largest bounding box (likely the main brand/name)
                        # result is (bbox, text, prob)
                        # bbox is a list of 4 coordinates [top-left, top-right, bottom-right, bottom-left]
                        
                        best_text = ""
                        max_area = 0
                        
                        for (bbox, text, prob) in results:
                            # Calculate area of bounding box
                            width = abs(bbox[1][0] - bbox[0][0])
                            height = abs(bbox[2][1] - bbox[1][1])
                            area = width * height
                            
                            if area > max_area and len(text) > 2: # Filter out tiny noise text
                                max_area = area
                                best_text = text
                                
                        if best_text:
                            # Clean the text to be a valid filename
                            clean_name = "".join(c for c in best_text if c.isalnum() or c in (' ', '_')).strip()
                            clean_name = clean_name.replace(" ", "_")
                            if clean_name:
                                group_name = clean_name
                                break # Stop after finding a name for this group
                except Exception as e:
                    print(f"OCR Error on {img}: {e}")
            
            print(f"Group {group_folder} identified as: {group_name}")
            
            # Now copy and rename all images in this group to the output directory
            for idx, img in enumerate(images_in_group):
                src = os.path.join(group_path, img)
                new_filename = f"{group_name}_{idx+1}.png"
                dst = os.path.join(output_dir, new_filename)
                
                # If name already exists, append more numbers
                counter = 1
                while os.path.exists(dst):
                    new_filename = f"{group_name}_{idx+1}_{counter}.png"
                    dst = os.path.join(output_dir, new_filename)
                    counter += 1
                
                shutil.copy2(src, dst)
                print(f"Renamed: {group_folder}/{img} -> {new_filename}")

if __name__ == "__main__":
    input_directory = "mosop_bg_removed"
    output_directory = "mosop_final_products"
    rename_images(input_directory, output_directory)
    print("Done. Check the 'mosop_final_products' folder.")
