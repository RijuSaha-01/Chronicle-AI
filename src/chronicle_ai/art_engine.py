"""
Chronicle AI - Art Engine
Handles communication with local Stable Diffusion API (ComfyUI or Automatic1111)
to generate cinematic cover art for diary episodes.
"""

import json
import os
import time
import logging
import requests
import uuid
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ArtEngine:
    def __init__(self, provider: str = "comfyui", base_url: str = "http://127.0.0.1:8188"):
        """
        Initialize ArtEngine.
        :param provider: 'comfyui' or 'automatic1111'
        :param base_url: The URL where SD is running
        """
        self.provider = provider.lower()
        self.base_url = base_url.rstrip("/")
        self.output_dir = "outputs/cover_art"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_cover(self, prompt: str, entry_id: Optional[int] = None) -> Optional[str]:
        """
        Generate an image based on the prompt and save it.
        Returns the path to the saved image.
        """
        logger.info(f"Generating cover art for prompt: {prompt[:50]}...")
        
        try:
            if self.provider == "comfyui":
                return self._generate_comfyui(prompt, entry_id)
            elif self.provider == "automatic1111":
                return self._generate_a1111(prompt, entry_id)
            else:
                logger.error(f"Unknown provider: {self.provider}")
                return None
        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            return None

    def _generate_a1111(self, prompt: str, entry_id: Optional[int]) -> Optional[str]:
        """Generate using Automatic1111 API."""
        payload = {
            "prompt": f"cinematic, highly detailed, masterpiece, {prompt}",
            "negative_prompt": "easynegative, worst quality, low quality, text, watermark, signature",
            "steps": 20,
            "cfg_scale": 7,
            "width": 1024,
            "height": 1024,
            "sampler_name": "Euler a"
        }
        
        response = requests.post(f"{self.base_url}/sdapi/v1/txt2img", json=payload)
        response.raise_for_status()
        
        import base64
        r = response.json()
        image_data = base64.b64decode(r['images'][0])
        
        filename = f"cover_{entry_id or uuid.uuid4()}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(image_data)
            
        return filepath

    def _generate_comfyui(self, prompt: str, entry_id: Optional[int]) -> Optional[str]:
        """
        Generate using ComfyUI API.
        Note: This is a simplified version. ComfyUI requires a full workflow JSON.
        We expect a basic txt2img workflow here.
        """
        # Minimalist Workflow for SDXL in ComfyUI
        # This is a placeholder for a real workflow JSON
        # In a real scenario, you'd load this from a template
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "cfg": 8,
                    "denoise": 1,
                    "latent_image": ["5", 0],
                    "model": ["4", 0],
                    "negative": ["7", 0],
                    "positive": ["6", 0],
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "seed": int(time.time()),
                    "steps": 20
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "sd_xl_base_1.0.safetensors"
                }
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "batch_size": 1,
                    "height": 1024,
                    "width": 1024
                }
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": f"cinematic, atmospheric, {prompt}"
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": "text, watermark, low quality, bad anatomy"
                }
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                }
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": f"chronicle_{entry_id or 'test'}",
                    "images": ["8", 0]
                }
            }
        }

        prompt_id = requests.post(f"{self.base_url}/prompt", json={"prompt": workflow}).json()["prompt_id"]
        
        # Poll for completion
        while True:
            history = requests.get(f"{self.base_url}/history/{prompt_id}").json()
            if prompt_id in history:
                break
            time.sleep(1)
            
        # Get the filename from history
        images = history[prompt_id]["outputs"]["9"]["images"]
        image_name = images[0]["filename"]
        
        # Download the image
        img_response = requests.get(f"{self.base_url}/view?filename={image_name}&type=output")
        
        filename = f"cover_{entry_id or uuid.uuid4()}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(img_response.content)
            
        return filepath

if __name__ == "__main__":
    # Test generation
    engine = ArtEngine(provider="comfyui") # Change to automatic1111 if needed
    print("Attempting test generation (ensure SD is running)...")
    try:
        path = engine.generate_cover("A moody cinematic landscape, 8k resolution, epic lighting")
        if path:
            print(f"Success! Image saved to: {path}")
    except Exception as e:
        print(f"Error: {e}")
        print("Troubleshooting Tip: Check if the API is enabled and the URL is correct.")
