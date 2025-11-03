from core.state import FlyerState
from typing import List
import torch
from diffusers import DiffusionPipeline

# Load Stable Diffusion globally
pipe = DiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    use_safetensors=True,
).to("cuda")
pipe.enable_xformers_memory_efficient_attention()


def parse_size(size_str: str) -> str:
    if not size_str:
        return "auto"
    size_str = str(size_str).strip()
    if size_str.endswith("%") or size_str.endswith("px"):
        return size_str
    try:
        return f"{float(size_str)}px"
    except ValueError:
        return "auto"


def extract_image_attributes(state: FlyerState):
    parsed = getattr(state, "theme_json", {}) or {}
    images = parsed.get("images", [])
    normalized_images = []

    if not isinstance(images, list) or not images:
        return {"count": 0, "images": []}

    for img in images:
        if not isinstance(img, dict):
            continue

        description = img.get("description", "").strip()
        position = img.get("position", "Center")
        size = parse_size(img.get("size", "auto"))

        pos_lower = position.lower()
        if "background" in pos_lower:
            layer = "background"
        elif "overlay" in pos_lower:
            layer = "overlay"
        else:
            layer = "foreground"

        normalized_images.append({
            "description": description,
            "position": position,
            "size": size,
            "layer": layer
        })

    return {"count": len(normalized_images), "images": normalized_images}


def image_generator_node(state: FlyerState) -> FlyerState:
    try:
        images_info = extract_image_attributes(state)
        num_images = images_info["count"]
        images_metadata = images_info["images"]

        generated_images: List[str] = []

        for i, img_meta in enumerate(images_metadata):
            prompt = f"{img_meta['description']} design for flyer, premium, elegant, professional"
            state.log(f"🖼️ Generating image {i+1}/{num_images}: {prompt}")

            img = pipe(
                prompt,
                num_inference_steps=30,
                guidance_scale=7.5,
            ).images[0]

            file_path = f"temp_flyer_image_{i}.png"
            img.save(file_path)
            generated_images.append(file_path)

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            state.log(f"✅ Generated image saved at {file_path}")

        # Inject images into HTML
        html = state.final_output or "<div></div>"
        POS_MAP = {
            "Top Left": (8, 8), "Top Center": (50, 8), "Top Right": (92, 8),
            "Center": (50, 50), "Bottom Left": (8, 92), "Bottom Center": (50, 92),
            "Bottom Right": (92, 92), "Left": (6, 50), "Right": (94, 50),
            "Top": (50, 6), "Bottom": (50, 94)
        }

        html_parts = html.split(">", 1)
        if len(html_parts) == 2:
            opening_div, rest_html = html_parts
            img_tags = ""
            for img_path, img_meta in zip(generated_images, images_metadata):
                xperc, yperc = POS_MAP.get(img_meta["position"], (50, 50))
                img_tags += f"""
                <img src="{img_path}" style="position:absolute; top:{yperc}%; left:{xperc}%;
                    width:{img_meta['size']}; height:{img_meta['size']}; transform:translate(-50%, -50%);
                    z-index:{2 if img_meta['layer']=='foreground' else 0}; pointer-events:none;"/>
                """
            state.refined_html = opening_div + ">" + img_tags + rest_html
        else:
            state.refined_html = html
            state.log("⚠️ Could not inject images into HTML, using original HTML")

        # Save generated images paths
        state.generated_images = generated_images

        # Optionally, update final_output for downstream steps
        state.final_output = state.refined_html or state.final_output

        state.log(f"🚀 Image generation and injection completed ({num_images} images).")

    except Exception as e:
        state.log(f"❌ [image_generator_node] Error: {str(e)}")

    return state
