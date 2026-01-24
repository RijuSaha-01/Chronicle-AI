"""
Chronicle AI - Image Client

Integration with Stable Diffusion backends (ComfyUI and Automatic1111)
for generating cinematic art and variations.
"""

import logging
import time
import os
import base64
import json
from typing import Optional, List, Dict, Any

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)

class ImageGenerator:
    """
    Client for generating images using Stable Diffusion backends.
    Supports both ComfyUI and Automatic1111.
    """

    def __init__(self, base_url: str, timeout: int = 120, default_model: Optional[str] = None, backend: str = "comfyui"):
        """
        Initialize the ImageGenerator.

        Args:
            base_url: The base URL of the SD backend (e.g., http://localhost:8188)
            timeout: Request timeout in seconds
            default_model: Name of the default model/checkpoint to use
            backend: The backend type ('comfyui' or 'automatic1111')
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_model = default_model
        self.backend = backend.lower()
        
        if self.backend not in ["comfyui", "automatic1111"]:
            logger.warning(f"Unsupported backend '{self.backend}', defaulting to 'comfyui'")
            self.backend = "comfyui"

    def _make_request(self, method: str, path: str, json_data: Optional[Dict] = None, params: Optional[Dict] = None) -> Any:
        """Helper to make HTTP requests with retry logic and error handling."""
        url = f"{self.base_url}{path}"
        
        # Simple retry logic
        for attempt in range(2):
            try:
                if HTTPX_AVAILABLE:
                    with httpx.Client(timeout=self.timeout) as client:
                        if method.upper() == "POST":
                            response = client.post(url, json=json_data, params=params)
                        else:
                            response = client.get(url, params=params)
                        response.raise_for_status()
                        return response.json()
                elif REQUESTS_AVAILABLE:
                    if method.upper() == "POST":
                        response = requests.post(url, json=json_data, params=params, timeout=self.timeout)
                    else:
                        response = requests.get(url, params=params, timeout=self.timeout)
                    response.raise_for_status()
                    return response.json()
                else:
                    raise RuntimeError("No HTTP library (httpx or requests) available")
            except Exception as e:
                if attempt == 1:
                    logger.error(f"Image generation request failed after retry: {e}")
                    raise
                logger.warning(f"Request attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(1)

    def check_health(self) -> bool:
        """
        Verify if the Stable Diffusion backend is running and accessible.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            if self.backend == "automatic1111":
                # A1111 health check
                path = "/sdapi/v1/progress"
                self._make_request("GET", path)
                return True
            else:
                # ComfyUI health check
                path = "/system_stats"
                self._make_request("GET", path)
                return True
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """
        List available model names from the backend.
        
        Returns:
            List[str]: A list of available model names
        """
        try:
            if self.backend == "automatic1111":
                models = self._make_request("GET", "/sdapi/v1/sd-models")
                return [m["title"] for m in models]
            else:
                # ComfyUI: Get models from CheckpointLoaderSimple node info
                info = self._make_request("GET", "/object_info/CheckpointLoaderSimple")
                return info.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [[]])[0]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    def generate(self, prompt: str, negative_prompt: str = "", width: int = 1280, height: int = 720, steps: int = 20, seed: Optional[int] = None) -> Optional[bytes]:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Positive prompt
            negative_prompt: Negative prompt
            width: Image width
            height: Image height
            steps: Number of sampling steps
            seed: Random seed (optional)

        Returns:
            Optional[bytes]: Raw image bytes or None if failed
        """
        if seed is None:
            seed = int(time.time())

        try:
            if self.backend == "automatic1111":
                return self._generate_a1111(prompt, negative_prompt, width, height, steps, seed)
            else:
                return self._generate_comfyui(prompt, negative_prompt, width, height, steps, seed)
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return None

    def _generate_a1111(self, prompt: str, negative_prompt: str, width: int, height: int, steps: int, seed: int) -> Optional[bytes]:
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": steps,
            "width": width,
            "height": height,
            "seed": seed,
            "cfg_scale": 7.0,
            "sampler_name": "Euler a"
        }
        if self.default_model:
             # A1111 requires setting the model via options if you want to change it
             # But usually you just use what's loaded. For now we assume loaded is fine
             pass
             
        res = self._make_request("POST", "/sdapi/v1/txt2img", json_data=payload)
        if res and "images" in res and len(res["images"]) > 0:
            return base64.b64decode(res["images"][0])
        return None

    def _generate_comfyui(self, prompt: str, negative_prompt: str, width: int, height: int, steps: int, seed: int) -> Optional[bytes]:
        # Minimalist Workflow for ComfyUI
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
                    "seed": seed,
                    "steps": steps
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": self.default_model or "sd_xl_base_1.0.safetensors"
                }
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "batch_size": 1,
                    "height": height,
                    "width": width
                }
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": prompt
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": negative_prompt
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
                    "filename_prefix": "chronicle_gen",
                    "images": ["8", 0]
                }
            }
        }

        prompt_res = self._make_request("POST", "/prompt", json_data={"prompt": workflow})
        prompt_id = prompt_res["prompt_id"]
        
        # Poll for completion
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            history = self._make_request("GET", f"/history/{prompt_id}")
            if prompt_id in history:
                images = history[prompt_id]["outputs"]["9"]["images"]
                image_name = images[0]["filename"]
                
                # Fetch the image
                url = f"{self.base_url}/view?filename={image_name}&type=output"
                if HTTPX_AVAILABLE:
                    with httpx.Client(timeout=30) as client:
                        img_res = client.get(url)
                        img_res.raise_for_status()
                        return img_res.content
                elif REQUESTS_AVAILABLE:
                    img_res = requests.get(url, timeout=30)
                    img_res.raise_for_status()
                    return img_res.content
            time.sleep(1)
            
        logger.error(f"ComfyUI generation timed out for prompt_id: {prompt_id}")
        return None

    def generate_variations(self, image_path: str, prompt: str, strength: float = 0.5) -> Optional[bytes]:
        """
        Generate image variations based on an existing image (img2img).

        Args:
            image_path: Path to the source image
            prompt: Positive prompt for the variation
            strength: Denoising strength (0.0 to 1.0)

        Returns:
            Optional[bytes]: Raw image bytes or None if failed
        """
        if not os.path.exists(image_path):
            logger.error(f"Source image not found: {image_path}")
            return None

        with open(image_path, "rb") as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')

        try:
            if self.backend == "automatic1111":
                payload = {
                    "init_images": [image_base64],
                    "prompt": prompt,
                    "denoising_strength": strength,
                    "steps": 20,
                    "cfg_scale": 7.0,
                    "sampler_name": "Euler a"
                }
                res = self._make_request("POST", "/sdapi/v1/img2img", json_data=payload)
                if res and "images" in res and len(res["images"]) > 0:
                    return base64.b64decode(res["images"][0])
            else:
                # ComfyUI variations (img2img)
                # Requires uploading the image first or using an absolute path if it is in the input folder
                # For simplicity, we assume we need to upload it.
                # ComfyUI's /upload/image endpoint
                files = {"image": (os.path.basename(image_path), image_data)}
                
                if HTTPX_AVAILABLE:
                    with httpx.Client(timeout=30) as client:
                        up_res = client.post(f"{self.base_url}/upload/image", files=files)
                        up_res.raise_for_status()
                        up_data = up_res.json()
                elif REQUESTS_AVAILABLE:
                    up_res = requests.post(f"{self.base_url}/upload/image", files=files, timeout=30)
                    up_res.raise_for_status()
                    up_data = up_res.json()
                else:
                    return None
                    
                uploaded_name = up_data["name"]
                
                # Use img2img workflow
                workflow = {
                    "3": {
                        "class_type": "KSampler",
                        "inputs": {
                            "cfg": 8,
                            "denoise": strength,
                            "latent_image": ["10", 0],
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
                            "ckpt_name": self.default_model or "sd_xl_base_1.0.safetensors"
                        }
                    },
                    "6": {
                        "class_type": "CLIPTextEncode",
                        "inputs": {
                            "clip": ["4", 1],
                            "text": prompt
                        }
                    },
                    "7": {
                        "class_type": "CLIPTextEncode",
                        "inputs": {
                            "clip": ["4", 1],
                            "text": "text, watermark, low quality"
                        }
                    },
                    "10": {
                        "class_type": "VAEEncode",
                        "inputs": {
                            "pixels": ["11", 0],
                            "vae": ["4", 2]
                        }
                    },
                    "11": {
                        "class_type": "LoadImage",
                        "inputs": {
                            "image": uploaded_name
                        }
                    },
                    "12": {
                        "class_type": "VAEDecode",
                        "inputs": {
                            "samples": ["3", 0],
                            "vae": ["4", 2]
                        }
                    },
                    "13": {
                        "class_type": "SaveImage",
                        "inputs": {
                            "filename_prefix": "chronicle_variation",
                            "images": ["12", 0]
                        }
                    }
                }
                
                prompt_res = self._make_request("POST", "/prompt", json_data={"prompt": workflow})
                prompt_id = prompt_res["prompt_id"]
                
                # Poll for completion
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    history = self._make_request("GET", f"/history/{prompt_id}")
                    if prompt_id in history:
                        images = history[prompt_id]["outputs"]["13"]["images"]
                        image_name = images[0]["filename"]
                        
                        # Fetch the image
                        url = f"{self.base_url}/view?filename={image_name}&type=output"
                        if HTTPX_AVAILABLE:
                            with httpx.Client(timeout=30) as client:
                                img_res = client.get(url)
                                return img_res.content
                        elif REQUESTS_AVAILABLE:
                            img_res = requests.get(url, timeout=30)
                            return img_res.content
                    time.sleep(1)
            return None
        except Exception as e:
            logger.error(f"Variation generation failed: {e}")
            return None
