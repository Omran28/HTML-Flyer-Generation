"""
Image Agent
- Reads image descriptions from theme_json.
- Generates images using Stable Diffusion.
- Saves images locally.
- *Enriches* the theme_json with the local image paths.
"""

from core.state import FlyerState
from typing import List
import torch, base64, os, mimetypes
from diffusers import DiffusionPipeline

# Load Stable Diffusion once globally
pipe = DiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    use_safetensors=True,
).to("cuda")
pipe.enable_xformers_memory_efficient_attention()


# -------------------------------
# Utilities
# -------------------------------
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
    """Convert image file to base64 URI for inline HTML embedding."""
    if not path or not os.path.exists(path):
        return ""
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{data}"


# -------------------------------
# Extract images from theme_json
# -------------------------------
def extract_image_attributes(state: FlyerState):
    parsed = getattr(state, "theme_json", {}) or {}
    images = parsed.get("images", [])
    normalized_images = []

    if not isinstance(images, list) or not images:
        return {"count": 0, "images": []}

    for img in images:
        if not isinstance(img, dict): continue

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


# -------------------------------
# Generate images and embed into HTML
# -------------------------------
def image_generator_node(state: FlyerState) -> FlyerState:
    try:
        images_info = extract_image_attributes(state)
        num_images = images_info["count"]
        images_metadata = images_info["images"]
        generated_images_data: List[dict] = []  # Stores the generated data

        for i, img_meta in enumerate(images_metadata):
            prompt = f"{img_meta['description']}, premium, elegant, professional flyer design"
            state.log(f"🖼️ Generating image {i + 1}/{num_images}: {prompt}")

            try:
                img = pipe(
                    prompt,
                    num_inference_steps=25,
                    guidance_scale=7.5,
                ).images[0]

                # Save image locally
                file_path = save_image_locally(img, i)
                data_uri = image_to_data_uri(file_path)  # For Streamlit preview

                # Prepare the data to enrich the JSON
                generated_images_data.append({
                    **img_meta,
                    "path": file_path,  # Relative path for HTML
                    "src": file_path,  # Alias for path
                    "preview_uri": data_uri  # Full Base64 for ST
                })

                if torch.cuda.is_available(): torch.cuda.empty_cache()
                state.log(f"✅ Generated image {i + 1} successfully.")

            except Exception as e:
                state.log(f"❌ Failed to generate image {i + 1}: {e}")

        # -------------------------------
        # --- MODIFIED: Enrich theme_json ---
        # Instead of injecting HTML, we update the JSON plan
        # -------------------------------

        json_images_list = state.theme_json.get("images", [])

        if len(generated_images_data) == len(json_images_list):
            for i, generated_data in enumerate(generated_images_data):
                # Add the new keys to the *original* JSON object
                json_images_list[i]["path"] = generated_data["path"]
                json_images_list[i]["src"] = generated_data["src"]

                # Truncate preview_uri for Streamlit display
                MAX_BASE64_LEN = 5000
                if len(generated_data["preview_uri"]) > MAX_BASE64_LEN:
                    preview = "data:image/png;base64,iVBORw0KGgoAAA..."
                else:
                    preview = generated_data["preview_uri"]

                json_images_list[i]["preview_uri"] = preview

            state.log(f"✅ Enriched state.theme_json with {len(generated_images_data)} image paths.")
        else:
            state.log(
                f"⚠️ Mismatch between images requested ({len(json_images_list)}) and generated ({len(generated_images_data)}). JSON enrichment skipped.")

        # -------------------------------
        # --- REMOVED: HTML Injection Logic ---
        # All the `html.split` and `img_tags` logic is GONE.
        # This agent no longer creates or modifies HTML.
        # -------------------------------

        # Save paths of generated images
        state.generated_images = [img["path"] for img in generated_images_data]
        state.log(f"🚀 Image generation completed ({len(generated_images_data)} images).")

        # --- REMOVED ---
        # save_html_final(state) 
        # This function is removed from this agent.

    except Exception as e:
        state.log(f"❌ [image_generator_node] Critical error: {e}")

    return state


# -------------------------------
# --- REMOVED: save_html_final ---
# This function has been moved to theme_agent.py
# -------------------------------

def save_image_locally(img, index=0, folder="flyer_images"):
    """Save PIL image to local disk and return relative path."""
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, f"flyer_img_{index}.png")
    img.save(file_path)
    return file_path