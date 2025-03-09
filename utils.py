import requests
import time

def fetch_and_verify_image(url):
    try:
        response = requests.get(url)
    except Exception as e:
        raise ValueError(e)
    
    if response.status_code != 200:
        raise ValueError("Status code 200")
    
    content_type = response.headers.get("Content-Type")
    if "image" not in content_type:
        raise ValueError("Requested url is not an image")
    
    return response.content


def generate_image():
    """ Simulate image generation (5 seconds) and return a base64-encoded image """
    time.sleep(5)  # Simulate processing delay
    image_str = "asdsaasdasd"
    return image_str
