import os, re, base64


# -------------------------------
# Conversion & parsing helpers
# -------------------------------
def safe_float(value, default=0.0):
    """Convert strings like '40%', 'px', 'width:40px' into float."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = \
        value.replace('%', '').replace('px', '').replace('width', '').replace('height', '').replace(',', '').split()[
            0].strip()
        try:
            return float(cleaned)
        except ValueError:
            return default
    return default


def get_position_coordinates(pos_name: str):
    """Convert fuzzy position strings to (x%, y%) coordinates."""
    if not pos_name: return 50, 50
    s = str(pos_name).lower()
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


def get_valid_color(color_str: str, default="#333333") -> str:
    if not color_str: return default
    if "gradient" in str(color_str).lower():
        match = re.search(r"#[0-9a-fA-F]{6}", color_str)
        return match.group(0) if match else default
    return color_str


def parse_size(size_str: str) -> str:
    if not size_str: return "auto"
    size_str = str(size_str).strip()
    if size_str.endswith("%") or size_str.endswith("px"): return size_str
    try:
        return f"{float(size_str)}px"
    except:
        return "auto"


# -------------------------------
# File & HTML helpers
# -------------------------------
def save_image_locally(img, index, folder="flyer_images"):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"flyer_img_{index}.png")
    img.save(path)
    return path.replace("\\", "/")


def get_image_base64(path: str):
    if not os.path.exists(path): return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def inject_images_for_preview(html_content: str) -> str:
    """Converts local image paths in HTML to Base64 data URIs for browser/Streamlit display."""
    matches = re.findall(r'src=["\'](flyer_images/[^"\']+)["\']', html_content)
    for img_path in set(matches):
        b64 = get_image_base64(img_path)
        if b64: html_content = html_content.replace(img_path, f"data:image/png;base64,{b64}")
    return html_content


def save_html(state_or_content, filename="flyer.html", content_override=None):
    """Saves HTML content, prioritizing content_override (used to save Base64-embedded previews)."""
    html = content_override or getattr(state_or_content, "html_refined", None) or getattr(state_or_content,
                                                                                          "html_final", None)
    if not html: return None
    os.makedirs("outputs", exist_ok=True)
    path = os.path.join("outputs", filename)
    with open(path, "w", encoding="utf-8") as f: f.write(html)
    return path


# -------------------------------
# 💡 NEW HELPER for Display Fix (Problem 2)
# -------------------------------
def inject_images_for_display(final_state):
    """
    Temporarily injects the actual <img> tags (reading position/size/radius)
    into the 'original' HTML (which only has placeholders) for the Streamlit preview.
    """
    html_content = final_state.html_final
    if not html_content or not getattr(final_state, "generated_images", None):
        return html_content

    temp_html = html_content
    theme_images_meta = final_state.theme_json.get("images", [])

    for idx, img in enumerate(final_state.generated_images):
        x, y = get_position_coordinates(img.get("pos", "center"))
        z_index = 0 if img.get("layer", "foreground") == "background" else 2
        size = parse_size(img.get("size", "40%"))

        # Read the border_radius from the theme JSON for dynamic shapes
        current_img_meta = theme_images_meta[idx] if idx < len(theme_images_meta) else {}
        border_radius = current_img_meta.get("border_radius", "10px")

        # Set z-index dynamically based on size/layer for stacking context
        z_index = 1 if '100%' in str(size) and 'background' in img.get("layer", "").lower() else 2

        img_tag = f'<img src="{img["path"]}" style="position:absolute;top:{y}%;left:{x}%;width:{size};height:{size};transform:translate(-50%,-50%);z-index:{z_index};pointer-events:none;border-radius:{border_radius};object-fit:cover;"/>'
        placeholder = f""

        # Replace the placeholder with the <img> tag
        temp_html = temp_html.replace(placeholder, img_tag)

    return temp_html