from core.state import FlyerState
from typing import List
import torch, base64, os, mimetypes
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


def image_to_data_uri(path: str) -> str:
    """Convert image file to base64 data URI for inline HTML embedding."""
    if not path or not os.path.exists(path):
        return ""
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{data}"


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

        generated_images: List[dict] = []

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

            # Convert image to base64 URI for embedding
            data_uri = image_to_data_uri(file_path)
            generated_images.append({**img_meta, "path": file_path, "data_uri": data_uri})

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            state.log(f"✅ Generated and embedded image {i+1} successfully.")

        # --- Inject images into HTML ---
        html = state.html_output or "<div></div>"
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
            for img_meta in generated_images:
                xperc, yperc = POS_MAP.get(img_meta["position"], (50, 50))
                z_index = 2 if img_meta["layer"] == "foreground" else 0

                img_tags += f"""
                <img src="{img_meta['data_uri']}" 
                     style="position:absolute; top:{yperc}%; left:{xperc}%;
                            width:{img_meta['size']}; height:{img_meta['size']};
                            transform:translate(-50%, -50%);
                            z-index:{z_index}; pointer-events:none; border-radius:10px;"/>
                """

            state.html_final = opening_div + ">" + img_tags + rest_html
        else:
            state.html_final = html
            state.log("⚠️ Could not inject images into HTML — using original HTML.")

        # Save results in state
        state.generated_images = [img["path"] for img in generated_images]
        state.log(f"🚀 Image generation & embedding completed ({num_images} images).")

    except Exception as e:
        state.log(f"❌ [image_generator_node] Error: {str(e)}")

    return state
