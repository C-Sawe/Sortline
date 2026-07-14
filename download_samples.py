import os
import requests

def download_image(url, filename):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"Downloaded: {filename}")
    else:
        print(f"Failed to download {url}")

def main():
    os.makedirs('sample_images', exist_ok=True)
    
    # Golden retriever 1
    download_image("https://images.unsplash.com/photo-1552053831-71594a27632d?auto=format&fit=crop&w=500&q=60", "sample_images/dog1.jpg")
    # Golden retriever 2
    download_image("https://images.unsplash.com/photo-1537151608804-ea6f1184efa7?auto=format&fit=crop&w=500&q=60", "sample_images/dog2.jpg")
    
    # Cat 1
    download_image("https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?auto=format&fit=crop&w=500&q=60", "sample_images/cat1.jpg")
    # Cat 2
    download_image("https://images.unsplash.com/photo-1495360010541-f48722b34f7d?auto=format&fit=crop&w=500&q=60", "sample_images/cat2.jpg")
    
    # Car
    download_image("https://images.unsplash.com/photo-1494976388531-d1058494cdd8?auto=format&fit=crop&w=500&q=60", "sample_images/car1.jpg")

if __name__ == "__main__":
    main()
