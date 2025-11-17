import os
import torch
from typing import List
from diffusers import DiffusionPipeline
from core.state import FlyerState

# ==========================================================
# Global Model Initialization
# ==========================================================
# Load Stable Diffusion once to avoid reloading on every run
try:
    pipe = DiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16,
        use_safetensors=True,
    ).to("cuda")
    pipe.enable_xformers_memory_efficient_attention()
except Exception as e:
    print(f"⚠️ Warning: Could not load Stable Diffusion on CUDA. Error: {e}")
    # Fallback or just pass if running locally without GPU for testing logic
    pipe = None


# ==========================================================
# Utilities
# ==========================================================
def parse_size(size_str: str) -> str:
    """Fixes the 'NameError' by defining this helper here."""
    if not size_str:
        return "auto"
    size_str = str(size_str).strip()
    if size_str.endswith("%") or size_str.endswith("px"):
        return size_str
    try:
        return f"{float(size_str)}px"
    except ValueError:
        return "auto"

def save_image_locally(img, index, folder="flyer_images"):
    """
    Saves the image to a folder and returns the relative path.
    This prevents the HTML file from becoming huge.
    """
    os.makedirs(folder, exist_ok=True)
    filename = f"flyer_img_{index}.png"
    file_path = os.path.join(folder, filename)
    img.save(file_path)
    return file_path

def save_html_final(state: FlyerState, filename="flyer_final.html") -> str:
    """Saves the modified HTML to disk."""
    if not hasattr(state, "html_final") or not state.html_final:
        # Fallback if html_final is empty, save html_output instead
        content = getattr(state, "html_output", "")
    else:
        content = state.html_final

    if not content:
        print("⚠️ No HTML content to save.")
        return ""

    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    return os.path.abspath(filename)

def extract_image_attributes(state: FlyerState):
    """Reads the plan from theme_json to know what images to generate."""
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


# ==========================================================
# Main Node Logic
# ==========================================================
def image_generator_node(state: FlyerState) -> FlyerState:
    try:
        # 1. Analyze requirements
        images_info = extract_image_attributes(state)
        num_images = images_info["count"]
        images_metadata = images_info["images"]

        generated_images_data = []

        # 2. Generate Images Loop
        for i, img_meta in enumerate(images_metadata):
            prompt = f"{img_meta['description']} design for flyer, premium, elegant, professional"
            state.log(f"🖼️ Generating image {i+1}/{num_images}: {prompt}")

            if pipe:
                try:
                    # Generate
                    img = pipe(
                        prompt,
                        num_inference_steps=25, # Lower steps for faster testing
                        guidance_scale=7.5,
                    ).images[0]

                    # SAVE LOCALLY (Fixes the "huge src" issue)
                    file_path = save_image_locally(img, index=i)

                    generated_images_data.append({
                        **img_meta,
                        "path": file_path,
                    })

                    state.log(f"✅ Generated image {i+1} saved to {file_path}")

                    # Clear GPU memory
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

                except Exception as e:
                    state.log(f"❌ SD Generation Error for image {i+1}: {e}")
            else:
                state.log("⚠️ Model not loaded, skipping generation (Mock Mode)")

        # 3. Inject Images into HTML (3-Node Workflow Style)
        html = state.html_output or "<div></div>"

        # Mapping for positions
        POS_MAP = {
            "Top Left": (8, 8), "Top Center": (50, 8), "Top Right": (92, 8),
            "Center": (50, 50), "Bottom Left": (8, 92), "Bottom Center": (50, 92),
            "Bottom Right": (92, 92), "Left": (6, 50), "Right": (94, 50),
            "Top": (50, 6), "Bottom": (50, 94)
        }

        # Split HTML to inject <img> tags
        html_parts = html.split(">", 1)

        if len(html_parts) == 2:
            opening_div, rest_html = html_parts
            img_tags = ""

            for img_data in generated_images_data:
                xperc, yperc = POS_MAP.get(img_data["position"], (50, 50))
                z_index = 0 if img_data["layer"] == "background" else 2

                # --- CRITICAL FIX: Use clean file path ---
                src_path = img_data["path"]

                img_tags += f"""
                <img src="{src_path}" 
                     style="position:absolute; top:{yperc}%; left:{xperc}%;
                            width:{img_data['size']}; height:{img_data['size']};
                            transform:translate(-50%, -50%);
                            z-index:{z_index}; pointer-events:none; border-radius:10px; object-fit:cover;"/>
                """

            # Reassemble HTML
            state.html_final = opening_div + ">" + img_tags + rest_html
        else:
            state.html_final = html
            state.log("⚠️ HTML structure invalid (no closing > found), skipping injection.")

        # 4. Save Final Results
        state.generated_images = [img["path"] for img in generated_images_data]

        output_path = save_html_final(state)
        state.log(f"💾 HTML with images saved to: {output_path}")

    except Exception as e:
        state.log(f"❌ [image_generator_node] Critical Error: {str(e)}")

    return state