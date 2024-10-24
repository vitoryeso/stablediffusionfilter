import time
import torch
import base64
from io import BytesIO
from PIL import Image
import PIL
from flask import Flask, request, jsonify
from flask_cors import CORS
from diffusers import AutoPipelineForText2Image
from diffusers import AutoPipelineForImage2Image
from diffusers.utils import load_image
import requests
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialize o modelo e pipeline
logger.info("Loading models...")
start_time = time.time()

# Load stable diffusion XL controlnet pipeline
# use from_pipe to avoid consuming additional memory when loading a checkpoint
pipeline_text2image = AutoPipelineForText2Image.from_pretrained("stabilityai/sdxl-turbo", torch_dtype=torch.float16, variant="fp16")
pipeline_text2image = pipeline_text2image.to("cuda")
pipeline_image2image = AutoPipelineForImage2Image.from_pipe(pipeline_text2image).to("cuda")

load_time = time.time() - start_time
logger.info(f"Models loaded in {load_time:.2f} seconds.")

app = Flask(__name__)
CORS(app)

# Função para converter imagem b64 para PIL
def b64_to_pil(image_b64):
    logger.info("Converting base64 to PIL...")
    start_time = time.time()
    image_data = base64.b64decode(image_b64)
    image = Image.open(BytesIO(image_data))
    conversion_time = time.time() - start_time
    logger.info(f"Base64 to PIL conversion took {conversion_time:.2f} seconds.")
    return image

# Função para converter PIL para b64
def pil_to_b64(image):
    logger.info("Converting PIL to base64...")
    start_time = time.time()
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    b64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
    conversion_time = time.time() - start_time
    logger.info(f"PIL to base64 conversion took {conversion_time:.2f} seconds.")
    return b64_image

# Função para redimensionar a imagem para um tamanho fixo (ex: 512x512)
def resize_image(image, target_size=(512, 512)):
    logger.info("Resizing image...")
    start_time = time.time()
    resized_image = image.resize(target_size, PIL.Image.Resampling.LANCZOS)
    resize_time = time.time() - start_time
    logger.info(f"Image resizing took {resize_time:.2f} seconds.")
    return resized_image

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        logger.info("Received request for image generation.")
        start_time = time.time()

        # Recebe a requisição JSON com o b64 e o prompt
        data = request.json
        #prompt = data.get('prompt', 'A girl holding a sign that says InstantX')
        prompt = data['prompt']
        src_img = data['control_image']

        # Converte a imagem b64 para PIL
        src_img = b64_to_pil(src_img)

        # Armazena o tamanho original da imagem de controle
        original_size = src_img.size

        # Redimensiona a imagem para o tamanho adequado para a rede (ex: 512x512)
        src_img_resized = resize_image(src_img)

        # Gera a imagem usando o modelo Stable Diffusion
        logger.info("Generating image with Stable Diffusion...")
        gen_start_time = time.time()
        generated_image = pipeline_image2image(prompt, image=src_img_resized, strength=0.5, guidance_scale=0.0, num_inference_steps=2).images[0]
        gen_time = time.time() - gen_start_time
        logger.info(f"Image generation took {gen_time:.2f} seconds.")

        # Redimensiona a imagem gerada para o tamanho original da imagem de controle
        generated_image_resized = generated_image.resize(original_size, PIL.Image.Resampling.LANCZOS)

        # Converte a imagem gerada redimensionada de volta para base64
        generated_image_b64 = pil_to_b64(generated_image_resized)

        total_time = time.time() - start_time
        logger.info(f"Total processing time: {total_time:.2f} seconds.")

        # Retorna a imagem gerada em b64
        return jsonify({"generated_image": generated_image_b64})

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
