from diffusers import StableDiffusionXLImg2ImgPipeline
import torch
from PIL import Image
import requests
from io import BytesIO

# Load the model with optimizations
model_id = "stabilityai/stable-diffusion-xl-base-1.0"
pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
    model_id, 
    torch_dtype=torch.float16,  # Reduces memory usage
    low_cpu_mem_usage=True  # Optimizes RAM
)

# Move the model to GPU
pipe.to("cuda")

# Enable memory optimizations
pipe.enable_xformers_memory_efficient_attention()  # Faster inference, less memory
pipe.enable_attention_slicing()  # Reduce VRAM spikes

# Resize to match SDXL requirements (1024x1024 or your custom size)

# Define the prompt and parameters
base_prompt = "Make it the face of a boy"
strength = 0.75  # How much the model modifies the image

image_url = "https://www.lumierebeautyclinic.com.au/wp-content/uploads/2023/05/how-to-make-yourself-pretty-Lumiere-Beauty-Clinic-scaled.jpg"
response = requests.get(image_url)
init_image = Image.open(BytesIO(response.content)).convert("RGB")
init_image = init_image.resize((1024, 1024))

# Define the prompt and parameters
base_prompt = "Make it the face of a boy"

prompt_variations = [
    f"{base_prompt}, ultra-detailed, cinematic lighting",
    f"{base_prompt}, surreal and dreamy, artistic brush strokes",
    f"{base_prompt}, futuristic and hyper-realistic, 8K resolution",
    f"{base_prompt}, in the style of a Renaissance painting",
    f"{base_prompt}, vibrant cyberpunk aesthetic, neon reflections"
]

for i, prompt in enumerate(prompt_variations):
    output_image = pipe(
        prompt=prompt, 
        image=init_image, 
        strength=strength, 
        num_inference_steps=40  # Higher steps for better quality
    ).images[0]
 
    print(f"Saving {i}")
    output_image.save(f"output_{i+1}.png")

print("All images generated successfully!")

