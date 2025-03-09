import boto3
import torch
import requests
from diffusers import StableDiffusionXLImg2ImgPipeline
from io import BytesIO
from PIL import Image

model_id = "stabilityai/stable-diffusion-xl-base-1.0"

AWS_STORAGE_BUCKET_NAME = "advisor-bucket"
AWS_ACCESS_KEY_ID = "AKIA47GCABVWGQ5KDECT"
AWS_SECRET_ACCESS_KEY = "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"
AWS_S3_REGION_NAME = "eu-north-1"
AWS_S3_ENDPOINT_URL = "https://advisor-bucket.s3.eu-north-1.amazonaws.com"

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_S3_REGION_NAME   
)

model_path = "ai_models/sdxl"

s3_model_path = "https://advisor-bucket.s3.eu-north-1.amazonaws.com/AI-Model/sdxl/"


base = StableDiffusionXLImg2ImgPipeline.from_pretrained(
    model_path, 
    variant="fp16", 
    use_safetensors=True
)
# base.unet = torch.compile(base.unet, mode="reduce-overhead", fullgraph=True)
base.to("cpu")


image_url = "https://www.lumierebeautyclinic.com.au/wp-content/uploads/2023/05/how-to-make-yourself-pretty-Lumiere-Beauty-Clinic-scaled.jpg"
response = requests.get(image_url)
init_image = Image.open(BytesIO(response.content)).convert("RGB")

prompt = "Make the image like an AI Image"

# Generate the new image
images = base(
    prompt=prompt, 
    image=init_image, 
    strength=0.7,
    guidance_scale=7.5,
).images

counter = 0

for image in images:
    print("Result --> ", image)
    # s3_client.put_object(
    # Bucket=AWS_STORAGE_BUCKET_NAME,
    # Key=f"ai-data",  # Path where the file will be stored
    # Body=image,  # The file content
    # ContentType=image.content_type  # Set correct content type
    # )
    # url = f"{AWS_S3_ENDPOINT_URL}/ai-data/"

    # Save the generated image
    image.save(f"output{counter}.png")
    counter += 1
