import os
import secrets
import time
import boto3
import torch
import requests
from io import BytesIO
from PIL import Image
from diffusers import StableDiffusionXLImg2ImgPipeline
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_ENDPOINT_URL= os.environ.get("AWS_S3_ENDPOINT_URL")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_S3_REGION_NAME   
)

class StabilityAIAdapter(object):
    strength = 0.75  # How much the model modifies the image
    emit = None
    sid = None

    def __init__(self):
        model_id = "stabilityai/stable-diffusion-xl-base-1.0"
        pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
            model_id, 
            torch_dtype=torch.float16,  # Reduces memory usage
            low_cpu_mem_usage=True  # Optimizes RAM
        )

        # Move the model to GPU
        pipe.to("cuda")
        self.pipe = pipe

    def enable_memory_efficiency(self):
        # Enable memory optimizations
        self.pipe.enable_xformers_memory_efficient_attention()  # Faster inference, less memory
        self.pipe.enable_attention_slicing()  # Reduce VRAM spikes
        print("Fastening Memory Efficiency")

    def add_image(self, image_url=None):
        if not image_url:
            image_url = "https://www.lumierebeautyclinic.com.au/wp-content/uploads/2023/05/how-to-make-yourself-pretty-Lumiere-Beauty-Clinic-scaled.jpg"
        
        response = requests.get(image_url)
        init_image = Image.open(BytesIO(response.content)).convert("RGB")
        init_image = init_image.resize((1024, 1024))
        return init_image
    
    def upload_to_s3(self, output_image, name):
        image_bytes = BytesIO()
        image_format = "JPEG"  # Change format if needed (e.g., PNG, JPEG)
        output_image.save(image_bytes, format=image_format)
        image_bytes.seek(0)  # Reset stream position

        path_name = "ai/repost"
        file_name = f"{name}-{secrets.token_hex(8)}"
        s3_client.put_object(
            Bucket=AWS_STORAGE_BUCKET_NAME,
            Key=f"{path_name}/{name}",  # Path where the file will be stored
            Body=image_bytes,  # The file content
            ContentType=f"image/{image_format.lower()}"  # Set correct content type
        )
        url = f"{AWS_S3_ENDPOINT_URL}/{path_name}/{file_name}"
        return url
    
    def emit_to_websocket(self, url):
        if not self.sid:
            raise ValueError("Provide sid adapter")

        if not self.emit:
            raise ValueError("Provide emit to adapter")
        
        data = {
            "message": "Sending Image Data to ws!",
            "sid": self.sid,
            "url": url,
        }
        self.emit("server", data, room=self.sid)

    def create_ai_images_and_send_to_websocket(self, prompt, image_url):
        if not self.sid:
            raise ValueError("Provide sid adapter")

        if not self.emit:
            raise ValueError("Provide emit to adapter")


        init_image = self.add_image(image_url)
        lst = []
        prompt_variations = [
            f"{prompt}, ultra-detailed, cinematic lighting",
            # f"{prompt}, surreal and dreamy, artistic brush strokes",
            # f"{prompt}, futuristic and hyper-realistic, 8K resolution",
            # f"{prompt}, in the style of a Renaissance painting",
            # f"{prompt}, vibrant cyberpunk aesthetic, neon reflections"
        ]

        for i, prompt in enumerate(prompt_variations):
            url = self.create_ai_image(prompt, init_image, i)
            self.emit_to_websocket(url)
            lst.append(url)

    def slow_recursive_function(self, n, start_time=None):
        if start_time is None:
            start_time = time.time()  # Set start time in first call
        
        # Base case: Stop after ~3 seconds
        if time.time() - start_time >= 3:
            return "Done"

        return self.slow_recursive_function(n + 1, start_time)  # Recursive call

    def slow_function(self):
        start_time = time.time()
        while time.time() - start_time < 3:
            pass

        print("Done")
        return "Done"

    def create_ai_image(self, prompt, image, i):
        output_image = self.pipe(
            prompt=prompt, 
            image=image, 
            strength=self.strength, 
            num_inference_steps=40  # Higher steps for better quality
        ).images[0]
    
        print(f"Saving {i}")
        url = self.upload_to_s3(output_image, f"output_{i+1}.jpeg")
        print("URL --> ", url)
        return url 



"""
{ 
    "event": "generate-ai-images", 
    "data": {
        "prompt": "Make it look more aesthetic",
        "image": "https://www.lumierebeautyclinic.com.au/wp-content/uploads/2023/05/how-to-make-yourself-pretty-Lumiere-Beauty-Clinic-scaled.jpg"
    } 
}

"""
