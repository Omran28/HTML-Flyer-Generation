import re
import os
import base64

# -------------------------------
# Safe conversions
# -------------------------------
def safe_float(value, default=0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = (
            value.replace('%','').replace('px','')
                 .replace('width','').replace('height','')
                 .replace(',', '').split()[0].strip()
        )
        try:
            return float(cleaned)
        except ValueError:
            return default
    return default

def parse_size(size_str: str) -> str:
    if not size_str: return "auto"
    size_str = str(size_str).strip()
    if size_str.endswith("%") or size_str.endswith("px"):
        return size_str
    try:
        return f"{float(size_str)}px"
    except ValueError:
        return "auto"

# -------------------------------
# Position mapping
# -------------------------------
def get_position_coordinates(pos_name: str):
    s = str(pos_name).lower().strip()
    POS_MAP = {
        "top left": (8, 8), "top center": (50, 8), "top right": (92, 8),
        "center": (50, 50), "bottom left": (8, 92), "bottom center": (50, 92), "bottom right": (92, 92),
        "left": (6, 50), "right": (94, 50), "top": (50, 6), "bottom": (50, 94)
    }
    for key, coord in POS_MAP.items():
        if key in s:
            return coord
    nums = re.findall(r"[\d.]+", s)
    if len(nums) >= 2:
        return float(nums[0]), float(nums[1])
    return 50, 50

# -------------------------------
# Color helper
# -------------------------------
def get_valid_color(color_str: str, default="#333333") -> str:
    if not color_str: return default
    if "gradient" in str(color_str).lower():
        match = re.search(r"#[0-9a-fA-F]{6}", color_str)
        return match.group(0) if match else default
    return color_str

# -------------------------------
# File & Base64 helpers
# -------------------------------
def save_image_locally(img, index, folder="flyer_images") -> str:
    os.makedirs(folder, exist_ok=True)
    filename = f"flyer_img_{index}.png"
    file_path = os.path.join(folder, filename)
    img.save(file_path)
    return file_path.replace("\\","/")

def get_image_base64(path: str):
    if not os.path.exists(path): return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def inject_images_for_preview(html_content: str) -> str:
    import re
    matches = re.findall(r'src=["\'](flyer_images/[^"\']+)["\']', html_content)
    preview_html = html_content
    for img_path in set(matches):
        if os.path.exists(img_path):
            b64_data = get_image_base64(img_path)
            if b64_data:
                preview_html = preview_html.replace(img_path, f"data:image/png;base64,{b64_data}")
    return preview_html

def save_html(content: str, folder="outputs", filename="flyer.html") -> str:
    if not content: return None
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
