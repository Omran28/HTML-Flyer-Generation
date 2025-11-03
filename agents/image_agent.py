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

        # Infer visual layer
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

    return {
        "count": len(normalized_images),
        "images": normalized_images
    }


def image_generator_node(state: FlyerState) -> FlyerState:
    try:
        images_info = extract_image_attributes(state)
        num_images = images_info["count"]
        images_metadata = images_info["images"]

        generated_images: List[dict] = []

        for i, img_meta in enumerate(images_metadata):
            prompt = f"{img_meta['description']} design for flyer, premium, elegant, professional"
            state.log(f"🖼️ Generating image {i+1}/{num_images}: {prompt}")

            img = pipe(
                prompt,
                num_inference_steps=30,
                guidance_scale=7.5,
            ).images[0]

            # Save temp file
            file_path = f"temp_flyer_image_{i}.png"
            img.save(file_path)

            generated_images.append({
                **img_meta,
                "path": file_path
            })
            torch.cuda.empty_cache()
            state.log(f"✅ Generated image saved at {file_path}")

        # Inject images into HTML without altering original final_output
        html = getattr(state, "final_output", "")
        width_px, height_px = 800, 600
        POS_MAP = {
            "Top Left": (8, 8), "Top Center": (50, 8), "Top Right": (92, 8),
            "Center": (50, 50), "Bottom Left": (8, 92), "Bottom Center": (50, 92),
            "Bottom Right": (92, 92), "Left": (6, 50), "Right": (94, 50),
            "Top": (50, 6), "Bottom": (50, 94)
        }

        # Split HTML after opening <div> to insert <img> tags
        html_parts = html.split(">", 1)
        if len(html_parts) == 2:
            opening_div, rest_html = html_parts
            img_tags = ""
            for img in generated_images:
                xperc, yperc = POS_MAP.get(img["position"], (50, 50))
                img_tags += f"""
                <img src="{img['path']}" style="position:absolute; top:{yperc}%; left:{xperc}%;
                    width:{img['size']}; height:{img['size']}; transform:translate(-50%, -50%);
                    z-index:{2 if img['layer']=='foreground' else 0}; pointer-events:none;"/>
                """
            # Save updated HTML in refined_html
            state.refined_html = opening_div + ">" + img_tags + rest_html
        else:
            state.refined_html = html
            state.log("⚠️ Could not inject images into HTML, using original HTML")

        # Save paths for later use
        state["generated_images"] = [img["path"] for img in generated_images]
        state.log(f"🚀 Image generation and injection completed ({num_images} images).")

    except Exception as e:
        state.log(f"❌ [image_generator_node] Error: {str(e)}")

    return state
