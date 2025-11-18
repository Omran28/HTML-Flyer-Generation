"""
agents/image_agent.py
---------------------
Image Generator Agent (3-Node Workflow)

• Generates images using Stable Diffusion.
• Saves images locally to 'flyer_images/' folder (Small HTML size).
• Injects <img> tags into the HTML skeleton created by the Theme Agent.
"""

import os
import torch
import re
from diffusers import DiffusionPipeline
from core.state import FlyerState

# ==========================================================
# Global Model Initialization
# ==========================================================
try:
    pipe = DiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16,
        use_safetensors=True,
    ).to("cuda")
    pipe.enable_xformers_memory_efficient_attention()
except Exception as e:
    print(f"⚠️ Warning: Could not load Stable Diffusion on CUDA. Error: {e}")
    pipe = None


# ==========================================================
# Utilities
# ==========================================================
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


def save_image_locally(img, index, folder="flyer_images"):
    """
    Saves image locally and returns a web-friendly path.
    CRITICAL: Replaces backslashes with forward slashes for HTML compatibility.
    """
    os.makedirs(folder, exist_ok=True)
    filename = f"flyer_img_{index}.png"
    file_path = os.path.join(folder, filename)
    img.save(file_path)
    # Force forward slashes (HTML standard) even on Windows
    return file_path.replace("\\", "/")


def save_html_final(state: FlyerState, filename="flyer_final.html") -> str:
    """Saves the final HTML with image links."""
    # Use refined HTML if available, otherwise final, otherwise output
    content = state.html_refined or state.html_final or getattr(state, "html_output", "")

    if not content:
        return ""

    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    return os.path.abspath(filename)


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

        # Infer layer based on position name
        pos_lower = str(position).lower()
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
            state.log(f"🖼️ Generating image {i + 1}/{num_images}: {prompt}")

            if pipe:
                try:
                    # Generate (Reduced steps for speed/stability)
                    img = pipe(
                        prompt,
                        num_inference_steps=25,
                        guidance_scale=7.5,
                    ).images[0]

                    # Save Locally
                    file_path = save_image_locally(img, index=i)

                    generated_images_data.append({
                        **img_meta,
                        "path": file_path,
                    })

                    state.log(f"✅ Generated image {i + 1} saved to {file_path}")

                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

                except Exception as e:
                    state.log(f"❌ SD Generation Error for image {i + 1}: {e}")
            else:
                state.log("⚠️ Model not loaded, skipping generation (Mock Mode)")

        # 3. Inject Images into HTML (3-Node Workflow)
        html = state.html_output or "<div></div>"

        # Smart Position Mapper (Matches Theme Agent logic)
        def get_pos_coords(pos_name):
            s = str(pos_name).lower().strip()
            # Custom regex check
            if "custom" in s or "%" in s:
                try:
                    nums = re.findall(r"[\d\.]+", s)
                    if len(nums) >= 2: return (float(nums[0]), float(nums[1]))
                except:
                    pass

            POS_MAP = {
                "top left": (8, 8), "top center": (50, 8), "top right": (92, 8),
                "center": (50, 50), "bottom left": (8, 92), "bottom center": (50, 92),
                "bottom right": (92, 92), "left": (6, 50), "right": (94, 50),
                "top": (50, 6), "bottom": (50, 94)
            }
            # Soft match
            for key, coords in POS_MAP.items():
                if key in s: return coords
            return (50, 50)

        # Inject Logic
        html_parts = html.split(">", 1)

        if len(html_parts) == 2:
            opening_div, rest_html = html_parts
            img_tags = ""

            for img_data in generated_images_data:
                xperc, yperc = get_pos_coords(img_data["position"])

                # Layering: Background (0), Overlay (1), Foreground (2). Text is usually (3).
                if img_data["layer"] == "background":
                    z_index = 0
                    # Make background cover full container if requested
                    style_dims = "width:100%; height:100%;" if "100%" in img_data[
                        "size"] else f"width:{img_data['size']}; height:{img_data['size']};"
                else:
                    z_index = 2
                    style_dims = f"width:{img_data['size']}; height:{img_data['size']};"

                src_path = img_data["path"]

                img_tags += f"""
                <img src="{src_path}" 
                     style="position:absolute; top:{yperc}%; left:{xperc}%;
                            {style_dims}
                            transform:translate(-50%, -50%);
                            z-index:{z_index}; pointer-events:none; border-radius:10px; object-fit:cover;"/>
                """

            # Reassemble
            state.html_final = opening_div + ">" + img_tags + rest_html
        else:
            state.html_final = html
            state.log("⚠️ HTML structure invalid (no closing > found), skipping injection.")

        # 4. Save Results
        state.generated_images = [img["path"] for img in generated_images_data]
        output_path = save_html_final(state)
        state.log(f"💾 HTML with images saved to: {output_path}")

    except Exception as e:
        state.log(f"❌ [image_generator_node] Critical Error: {str(e)}")

    return state