import io
from diffusers import DiffusionPipeline
import torch
import requests
from io import BytesIO
from PIL import Image

url = "https://www.lumierebeautyclinic.com.au/wp-content/uploads/2023/05/how-to-make-yourself-pretty-Lumiere-Beauty-Clinic-scaled.jpg"
response = requests.get(url)
init_image = Image.open(BytesIO(response.content)).convert("RGB")

# load both base & refiner
base = DiffusionPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0", 
	torch_dtype=torch.float16, 
	variant="fp16", 
	use_safetensors=True,
)
base.to("cuda")
refiner = DiffusionPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-refiner-1.0",
    text_encoder_2=base.text_encoder_2,
    vae=base.vae,
    torch_dtype=torch.float16,
    use_safetensors=True,
    variant="fp16",
)
refiner.to("cuda")

# Define how many steps and what % of steps to be run on each experts (80/20) here
n_steps = 40
high_noise_frac = 0.8

# prompt = "A majestic lion jumping from a big stone at night"
prompt = "Make it more aesthetic"

# run both experts
image = refiner(
    prompt=prompt,
    num_inference_steps=n_steps,
    denoising_start=high_noise_frac,
    image=init_image,
).images[0]

image.save("output.png")
