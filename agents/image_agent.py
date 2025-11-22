import os
import re
import torch
from diffusers import DiffusionPipeline
from core.state import FlyerState
import base64

# Initialize Stable Diffusion once
pipe = DiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    use_safetensors=True
)
pipe.to("cuda")


# -------------------------------
# "Utilities"
# -------------------------------

def parse_size(size_str: str) -> str:
    """Normalize size to pixels or keep as-is if % or px."""
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
    """Save generated image and return local path."""
    os.makedirs(folder, exist_ok=True)
    filename = f"flyer_img_{index}.png"
    file_path = os.path.join(folder, filename)
    img.save(file_path)
    return file_path.replace("\\", "/")


def save_html(state: FlyerState, filename="flyer_output.html", html_attr="html_final", content_override=None) -> str:
    content = content_override if content_override is not None else getattr(state, html_attr, "")
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(filename)



def get_image_base64(path: str):
    """Return image as base64 string for HTML preview."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def inject_images_for_preview(html_content: str) -> str:
    """Replace <img src="flyer_images/..."> paths with base64 for Streamlit display."""
    matches = re.findall(r'src=["\'](flyer_images/[^"\']+)["\']', html_content)
    preview_html = html_content

    for img_path in set(matches):
        local_path = img_path.replace("/", os.sep).replace("\\", os.sep)
        if os.path.exists(local_path):
            b64_data = get_image_base64(local_path)
            if b64_data:
                preview_html = preview_html.replace(img_path, f"data:image/png;base64,{b64_data}")

    return preview_html


# -------------------------------
# "Image Generator Node"
# -------------------------------

def extract_image_attributes(state: FlyerState):
    """Normalize image info from theme_json."""
    parsed = getattr(state, "theme_json", {}) or {}
    images = parsed.get("images", [])
    normalized_images = []

    for img in images:
        if not isinstance(img, dict):
            continue

        description = img.get("description", "").strip()
        position = img.get("position", "Center")
        size = parse_size(img.get("size", "auto"))

        # Layer based on position
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


def get_position_coordinates(pos_name: str):
    """Convert position string to (x%, y%) coordinates."""
    s = str(pos_name).lower().strip()
    POS_MAP = {
        "top left": (8, 8), "top center": (50, 8), "top right": (92, 8),
        "center": (50, 50), "bottom left": (8, 92), "bottom center": (50, 92),
        "bottom right": (92, 92), "left": (6, 50), "right": (94, 50),
        "top": (50, 6), "bottom": (50, 94)
    }
    for key, coord in POS_MAP.items():
        if key in s:
            return coord
    # Custom numeric positions
    nums = re.findall(r"[\d.]+", s)
    if len(nums) >= 2:
        return float(nums[0]), float(nums[1])
    return 50, 50


def image_generator_node(state: FlyerState) -> FlyerState:
    """Generate images, inject into HTML, save results."""
    try:
        images_info = extract_image_attributes(state)
        generated_images_data = []

        for i, img_meta in enumerate(images_info["images"]):
            prompt = f"{img_meta['description']} design for flyer, premium, elegant, professional"
            state.log(f"🖼️ Generating image {i + 1}/{images_info['count']}: {prompt}")

            if pipe:
                try:
                    img = pipe(prompt, num_inference_steps=25, guidance_scale=7.5).images[0]
                    file_path = save_image_locally(img, i)
                    generated_images_data.append({**img_meta, "path": file_path})
                    state.log(f"✅ Generated image {i + 1} saved to {file_path}")

                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception as e:
                    state.log(f"❌ SD Generation Error for image {i + 1}: {e}")
            else:
                state.log("⚠️ Model not loaded, skipping generation (Mock Mode)")

        # Inject <img> tags into html_output -> html_final
        html = state.html_output
        img_tags = ""
        for img_data in generated_images_data:
            x, y = get_position_coordinates(img_data["position"])
            z_index = 0 if img_data["layer"] == "background" else 2
            style_dims = "width:100%; height:100%;" if img_data["layer"] == "background" else f"width:{img_data['size']}; height:{img_data['size']};"
            img_tags += f"""
            <img src="{img_data['path']}" 
                 style="position:absolute; top:{y}%; left:{x}%;
                        {style_dims}
                        transform:translate(-50%, -50%);
                        z-index:{z_index}; pointer-events:none; border-radius:10px; object-fit:cover;"/>
            """

        # Inject before closing </div>
        if html.endswith("</div>"):
            state.html_final = html.replace("</div>", img_tags + "</div>")
        else:
            state.html_final = html + img_tags

        state.generated_images = [img["path"] for img in generated_images_data]

        # Save HTML with images embedded
        original_with_images = inject_images_for_preview(state.html_final)
        output_path = save_html(state, filename="flyer_original.html", html_attr=None, content_override=original_with_images)
        state.log(f"💾 HTML with images saved to: {output_path}")



    except Exception as e:
        state.log(f"❌ [image_generator_node] Critical Error: {str(e)}")

    return state
