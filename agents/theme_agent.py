"""
Theme Agent (and HTML Assembler)
- Analyzes user prompt to create theme_json (the "plan").
- Assembles the final HTML from the *enriched* theme_json (after images are generated).
"""

import os, re, json
from core.state import FlyerState
from models.llm_model import initialize_llm
from utils.prompt_utils import THEME_ANALYZER_PROMPT

# Safe utility for numeric conversion
def safe_float(value, default=0.0):
    """Convert strings like '85%' or '100px' safely to float, fallback to default."""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.replace('%', '').replace('px', '').split()[0].strip()
            return float(cleaned)
    except:
        return default
    return default

# --- NEWLY ADDED FUNCTION ---
# This was missing, causing the NameError
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
# --- END OF ADDED FUNCTION ---

# Utility to support 'custom (x%, y%)' positions
def get_position(pos_str: str):
    """Resolve position strings including custom (x%, y%)."""
    POS_MAP = {
        "Top Left": (8, 8), "Top Center": (50, 8), "Top Right": (92, 8),
        "Center": (50, 50), "Bottom Left": (8, 92), "Bottom Center": (50, 92),
        "Bottom Right": (92, 92), "Left": (6, 50), "Right": (94, 50),
        "Top": (50, 6), "Bottom": (50, 94)
    }
    if str(pos_str).startswith("custom"):
        try:
            coords = pos_str.strip().split("(")[-1].strip(")").split(",")
            xperc = float(coords[0].replace("%", "").strip())
            yperc = float(coords[1].replace("%", "").strip())
            return (xperc, yperc)
        except:
            return (50, 50)  # fallback to center on malformed custom input
    return POS_MAP.get(pos_str, (50, 50))


# --- (The rest of the file remains exactly the same) ---


def generate_flyer_html(parsed: dict) -> str:
    """
    Generate flyer HTML from *enriched* theme JSON (with image paths).
    Handles background image, text hierarchy, shapes, layering, and decorative images.
    """
    theme = parsed.get("theme", {})
    texts = parsed.get("texts", [])
    layout = parsed.get("layout", {})
    shapes = layout.get("layout_shapes", [])
    images = parsed.get("images", [])

    width_px, height_px = 800, 600

    # --- Separate Background Image from other images ---
    bg_image_path = ""
    decorative_images = []
    if isinstance(images, list):
        for img in images:
            if img.get("position") == "Background" or "background" in str(img.get("position")).lower():
                bg_image_path = img.get("path", "")
            else:
                decorative_images.append(img)

    # --- Set background style ---
    bg_color = layout.get("background", {}).get("color", theme.get("theme_colors", ["#FFFFFF"])[0])

    if bg_image_path:
        bg_style = f"background-image: url('{bg_image_path}'); background-size: cover; background-position: center;"
    else:
        bg_style = f"background:{bg_color};"


    html_parts = [
        f"""<div style="width:{width_px}px; height:{height_px}px; border-radius:20px; overflow:hidden;
                        position:relative; {bg_style} font-family:sans-serif;">"""
    ]

    # -- Shapes --
    for shape in shapes:
        s_type = shape.get("shape", "rectangle")
        pos = shape.get("position", "Center")
        s_size = shape.get("size", "40%")
        s_color = shape.get("color", "#FFFFFF")
        s_opacity = safe_float(shape.get("opacity", 0.9), 0.9)
        s_layer = shape.get("layer", "background")

        xperc, yperc = get_position(pos)
        z_index = 0 if s_layer == "background" else 1
        w = h = s_size if "px" in str(s_size) else f"{safe_float(s_size, 40)}%"
        border_radius = {"circle": "50%", "floral": "50%", "sticker": "20px"}.get(s_type, "15px")

        html_parts.append(f"""
        <div style="position:absolute; top:{yperc}%; left:{xperc}%;
                    width:{w}; height:{h}; background:{s_color};
                    opacity:{s_opacity}; border-radius:{border_radius};
                    box-shadow:0 12px 30px rgba(0,0,0,0.15);
                    transform:translate(-50%, -50%);
                    z-index:{z_index};"></div>
        """)

    # -- Decorative Images (Non-Background) --
    for img in decorative_images:
        src = img.get("path", "")
        if not src:
            continue
        pos = img.get("position", "Center")
        size = img.get("size", "100%")
        layer = img.get("layer", "overlay") # Default to overlay

        xperc, yperc = get_position(pos)
        z_index = {"background": 0, "overlay": 1, "foreground": 2}.get(layer, 1)

        # --- THIS LINE BELOW IS THE ONE THAT CAUSED THE ERROR ---
        # It now works because parse_size is defined above
        img_size = parse_size(size)

        html_parts.append(f"""
        <img src="{src}" style="position:absolute; top:{yperc}%; left:{xperc}%;
             width:{img_size}; height:{img_size}; transform:translate(-50%, -50%);
             z-index:{z_index}; pointer-events:none; border-radius:10px; object-fit: contain;"/>
        """)

    # -- Texts --
    for t in texts:
        if not isinstance(t, dict):
            continue
        content = t.get("content", "")
        font_style = t.get("font_style", "sans-serif")
        font_size = t.get("font_size", "40px")
        color = t.get("font_color", "#000000")
        angle = t.get("angle", "0deg")
        style_list = t.get("style", []) or []
        pos = t.get("position", "Center")
        layer = t.get("layer", "foreground")

        xperc, yperc = get_position(pos)
        z_index = 3 if layer == "foreground" else 2 # Text is always on top
        font_weight = "700" if "bold" in style_list else "400"
        font_style_css = "italic" if "italic" in style_list else "normal"

        shadows = []
        if "shadow" in style_list:
            shadows.append("2px 4px 12px rgba(0,0,0,0.35)")
        if "glow" in style_list:
            shadows.append("0 0 12px rgba(255,255,255,0.35)")
        text_shadow_css = ", ".join(shadows) if shadows else "none"

        gradient_css = (
            "background: linear-gradient(90deg, #388E3C, #A5D6A7); -webkit-background-clip: text; color: transparent;"
            if "gradient" in style_list or "gradient(" in str(color)
            else f"color:{color};"
        )

        html_parts.append(f"""
        <div style="position:absolute; top:{yperc}%; left:{xperc}%;
                    transform:translate(-50%, -50%) rotate({angle});
                    font-family:{font_style}; font-size:{font_size}; font-weight:{font_weight};
                    font-style:{font_style_css}; {gradient_css}; text-shadow:{text_shadow_css};
                    z-index:{z_index}; text-align:center; white-space:nowrap;">
          {content}
        </div>
        """)

    html_parts.append("</div>")
    return "\n".join(html_parts)


# -------------------------------
# Node 1: Theme Analyzer (The "Plan")
# -------------------------------
def theme_analyzer_node(state: FlyerState) -> FlyerState:
    """Analyze theme, generate JSON plan, and store in state."""
    state.log("🎨 Analyzing theme... (Creating JSON plan)")

    user_prompt = state.user_prompt.strip()
    if not user_prompt:
        state.log("❌ Empty prompt. Skipping theme analysis.")
        state.theme_json = {"error": "Empty prompt."}
        return state

    llm = initialize_llm()
    llm_prompt = THEME_ANALYZER_PROMPT.replace("{user_prompt}", user_prompt)
    state.log(f"⚙️ Using Gemini model for theme analysis.")

    try:
        response = llm.invoke(llm_prompt)
        raw_output = getattr(response, "content", str(response)).strip()
        cleaned = re.sub(r"^```(?:json)?|```$", "", raw_output, flags=re.MULTILINE)
        parsed = json.loads(cleaned)

        required_keys = ["theme", "texts", "layout", "images"]
        missing = [k for k in required_keys if k not in parsed]
        if missing:
            raise ValueError(f"Missing keys in LLM output: {missing}")

        state.theme_json = parsed
        state.log("✅ Theme analysis completed. JSON plan generated.")

    except json.JSONDecodeError:
        err = "❌ Failed to decode JSON from Gemini output."
        state.log(err)
        state.theme_json = {"error": "Invalid JSON structure"}

    except Exception as e:
        err = f"❌ Unexpected error during theme generation: {e}"
        state.log(err)
        state.theme_json = {"error": str(e)}

    return state

# -------------------------------
# HTML Saving Utility
# -------------------------------
def save_html_final(state: FlyerState, filename="flyer_final.html") -> str:
    if not hasattr(state,"html_final") or not state.html_final:
        raise ValueError("No HTML in state.html_final to save.")
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    with open(filename,"w",encoding="utf-8") as f:
        f.write(state.html_final)
    return os.path.abspath(filename)


# -------------------------------
# Node 3: HTML Assembler (The "Build")
# -------------------------------
def assembler_node(state: FlyerState) -> FlyerState:
    """
    Assembles the final HTML from the *enriched* theme_json
    (which now contains image paths).
    """
    state.log("🧩 Assembling HTML... (Building from enriched JSON)")

    if not state.theme_json:
        state.log("❌ Cannot assemble HTML: theme_json is empty.")
        state.error = "theme_json is empty"
        return state

    try:
        # This function builds the HTML from the *complete* JSON plan
        html_content = generate_flyer_html(state.theme_json)

        state.html_output = html_content
        state.html_final = html_content # This is the "base" HTML for refinement

        # Save the first assembled version
        save_path = save_html_final(state)
        state.log(f"✅ HTML assembled and saved to {save_path}")

    except Exception as e:
        err = f"❌ Failed to assemble HTML: {e}"
        state.log(err)
        state.error = str(e)

    return state