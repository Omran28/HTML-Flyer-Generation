import os, re, json
from core.state import FlyerState
from models.llm_model import initialize_llm
from utils.prompt_utils import THEME_ANALYZER_PROMPT

def safe_float(value, default=0.0):
    """Extract a float from various string formats like '40%', 'px', 'width:40px'."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = (
            value.replace('%', '').replace('px', '')
                 .replace('width', '').replace('height', '')
                 .replace(',', '').split()[0].strip()
        )
        try:
            return float(cleaned)
        except ValueError:
            return default
    return default

def get_position(pos_str: str):
    """Convert fuzzy or custom position strings into (x%, y%) coordinates."""
    if not pos_str:
        return 50, 50
    s = str(pos_str).lower()
    if "custom" in s or "%" in s:
        nums = re.findall(r"[\d.]+", s)
        if len(nums) >= 2:
            return float(nums[0]), float(nums[1])
    # Predefined positions
    mapping = {
        "top left": (8, 8), "top center": (50, 8), "top right": (92, 8),
        "center": (50, 50), "bottom left": (8, 92), "bottom center": (50, 92),
        "bottom right": (92, 92), "left": (6, 50), "right": (94, 50),
        "top": (50, 6), "bottom": (50, 94)
    }
    for key, val in mapping.items():
        if key in s: return val
    return 50, 50

def get_valid_color(color_str: str, default="#333333") -> str:
    if not color_str: return default
    if "gradient" in str(color_str).lower():
        match = re.search(r"#[0-9a-fA-F]{6}", color_str)
        return match.group(0) if match else default
    return color_str

def generate_flyer_html(parsed: dict) -> str:
    """
    Generate creative flyer HTML from LLM JSON.
    - Background shapes (waves, rectangles, circles)
    - Foreground images (dynamic positioning)
    - Texts (headings, subtitles, CTA)
    - Overlay effects (shadow, glow, gradient)
    """
    theme = parsed.get("theme", {})
    texts = parsed.get("texts", [])
    images = parsed.get("images", [])
    layout = parsed.get("layout", {})
    shapes = layout.get("layout_shapes", [])

    width_px, height_px = 800, 600
    bg_color = layout.get("background", {}).get("color", theme.get("theme_colors", ["#F8FBF8"])[0])

    html_parts = [
        f"""<div style="width:{width_px}px; height:{height_px}px; border-radius:20px; overflow:hidden;
                        position:relative; background:{bg_color}; font-family:sans-serif;">""",
        # Global gradient definitions
        """
        <svg width="0" height="0" style="position:absolute">
          <defs>
            <linearGradient id="g1" x1="0" x2="1" y1="0" y2="1">
              <stop offset="0%" stop-color="#A5D6A7"/>
              <stop offset="100%" stop-color="#388E3C"/>
            </linearGradient>
          </defs>
        </svg>
        """
    ]

    # ---------------------------
    # Background Shapes / Layers
    # ---------------------------
    for shape in shapes:
        s_type = shape.get("shape", "rectangle")
        s_pos = shape.get("position", "Center")
        s_size = shape.get("size", "40%")
        s_color = get_valid_color(shape.get("color", "#FFFFFF"))
        s_opacity = min(safe_float(shape.get("opacity", 0.9), 0.9), 0.6)
        x, y = get_position(s_pos)
        z_index = 0
        w = h = s_size if "px" in str(s_size) else f"{safe_float(s_size, 40)}%"

        if s_type == "wave":
            pos_style = "bottom:0;" if "bottom" in str(s_pos).lower() else "top:0;"
            html_parts.append(f"""
            <svg viewBox="0 0 800 240" preserveAspectRatio="none"
                 style="position:absolute; left:10%; width:80%; height:40%; {pos_style}
                        z-index:{z_index}; opacity:{s_opacity};">
              <path d="M0,120 C200,40 400,200 800,120 L800,240 L0,240 Z" fill="{s_color}"/>
            </svg>""")
            continue

        border_radius = {"circle": "50%", "floral": "50%", "sticker": "20px"}.get(s_type, "15px")
        html_parts.append(f"""
        <div style="position:absolute; top:{y}%; left:{x}%;
                    width:{w}; height:{h}; background:{s_color};
                    opacity:{s_opacity}; border-radius:{border_radius};
                    box-shadow:0 12px 30px rgba(0,0,0,0.15);
                    transform:translate(-50%, -50%);
                    z-index:{z_index};"></div>
        """)

    # ---------------------------
    # Foreground Images
    # ---------------------------
    for idx, img in enumerate(images):
        if not isinstance(img, dict): continue
        path = img.get("path", "")
        if not path: continue
        x, y = get_position(img.get("position", "Center"))
        size = img.get("size", "40%")
        width = height = size if "%" in str(size) else f"{safe_float(size, 40)}%"
        z_index = 2 if "background" not in img.get("layer", "foreground") else 0

        html_parts.append(f"""
        <img src="{path}" 
             style="position:absolute; top:{y}%; left:{x}%;
                    width:{width}; height:{height};
                    transform:translate(-50%, -50%);
                    z-index:{z_index}; border-radius:15px; object-fit:cover;"/>
        """)

    # ---------------------------
    # Text Layers
    # ---------------------------
    for t in texts:
        if not isinstance(t, dict): continue
        content = t.get("content", "")
        font_style = t.get("font_style", "sans-serif")
        font_size = t.get("font_size", "40px")
        color = t.get("font_color", "#000000")
        angle = t.get("angle", "0deg")
        style_list = t.get("style", []) or []
        pos = t.get("position", "Center")
        text_shape = t.get("text_shape", "straight")
        x, y = get_position(pos)

        z_index = 3
        font_weight = "700" if "bold" in style_list else "400"
        font_style_css = "italic" if "italic" in style_list else "normal"

        shadows = []
        if "shadow" in style_list: shadows.append("2px 4px 12px rgba(0,0,0,0.35)")
        if "glow" in style_list: shadows.append("0 0 12px rgba(255,255,255,0.35)")
        text_shadow_css = ", ".join(shadows) if shadows else "none"

        gradient_css = (
            "background: linear-gradient(90deg, #388E3C, #A5D6A7); -webkit-background-clip: text; color: transparent;"
            if "gradient" in style_list or "gradient(" in str(color)
            else f"color:{color};"
        )

        if text_shape == "curved":
            # Curved text as SVG path
            fs = int(str(font_size).replace("px", "") or 40)
            radius = max(80, fs*2 + 20)
            path_id = f"curve_path_{idx}"
            html_parts.append(f"""
            <svg style="position:absolute; left:0; top:0; width:{width_px}px; height:{height_px}px; z-index:{z_index}; pointer-events:none;">
              <defs><path id="{path_id}" d="M {width_px/2-radius} {height_px/2} A {radius} {radius} 0 0 1 {width_px/2+radius} {height_px/2}" /></defs>
              <text style="font-family:{font_style}; font-size:{font_size}; font-weight:{font_weight}; font-style:{font_style_css};">
                <textPath href="#{path_id}" startOffset="50%" text-anchor="middle" style="fill:{color}; text-shadow:{text_shadow_css};">
                  {content}
                </textPath>
              </text>
            </svg>
            """)
            continue

        html_parts.append(f"""
        <div style="position:absolute; top:{y}%; left:{x}%;
                    transform:translate(-50%, -50%) rotate({angle});
                    font-family:{font_style}; font-size:{font_size}; font-weight:{font_weight};
                    font-style:{font_style_css}; {gradient_css}; text-shadow:{text_shadow_css};
                    z-index:{z_index}; text-align:center; white-space:nowrap;">
          {content}
        </div>
        """)

    # ---------------------------
    # Premium overlay for depth
    # ---------------------------
    html_parts.append("""
    <div style="position:absolute; inset:0; border-radius:20px;
                box-shadow: inset 0 0 80px rgba(255,255,255,0.03),
                            inset 0 -30px 80px rgba(0,0,0,0.06);
                z-index:10; pointer-events:none;"></div>
    """)
    html_parts.append("</div>")  # Closing main div
    return "\n".join(html_parts)

def theme_analyzer_node(state: FlyerState) -> FlyerState:
    user_prompt = state.user_prompt.strip()
    if not user_prompt:
        state.log("❌ Empty prompt. Skipping theme analysis.")
        state.theme_json = {"error": "Empty prompt."}
        return state

    llm = initialize_llm()
    llm_prompt = THEME_ANALYZER_PROMPT.replace("{user_prompt}", user_prompt)
    state.log("⚙️ Using Gemini model for theme analysis.")

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
        state.html_output = generate_flyer_html(parsed)
        state.log("✅ Theme analysis completed. JSON plan & creative HTML generated.")

    except Exception as e:
        state.log(f"❌ Error during theme generation: {e}")
        state.theme_json = {"error": str(e)}
        state.html_output = "<p style='color:red'>Error generating flyer theme.</p>"

    return state
