"""
agents/theme.py
----------------
Theme Analyzer Agent

• Generates flyer layout & theme using LLM.
• Builds a visually striking HTML layout with shapes, text, and background.
• Supports premium layering, gradients, shadows, and curved/sticker text.
"""

import os, re, json
from html2image import Html2Image
from core.state import FlyerState
from models.llm_model import initialize_llm
from utils.prompt_utils import THEME_ANALYZER_PROMPT


# ==========================================================
# Utility
# ==========================================================
def safe_float(value, default=0.0):
    """Convert strings like '85%' or '100px' safely to float, fallback to default."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = (
            value.replace('%', '')
                 .replace('width', '')
                 .replace('height', '')
                 .replace(',', '')
                 .split()[0]
                 .strip()
        )
        try:
            return float(cleaned)
        except ValueError:
            return default
    return default


# ==========================================================
# HTML Generator
# ==========================================================
def generate_flyer_html(parsed: dict) -> str:
    """Generate premium flyer HTML from parsed theme data."""
    theme = parsed.get("theme", {})
    texts = parsed.get("texts", [])
    layout = parsed.get("layout", {})
    shapes = layout.get("layout_shapes", [])

    width_px, height_px = 800, 600
    bg_color = layout.get("background", {}).get("color", theme.get("theme_colors", ["#FFFFFF"])[0])

    html_parts = [
        f"""<div style="width:{width_px}px; height:{height_px}px; border-radius:20px; overflow:hidden;
                        position:relative; background:{bg_color}; font-family:sans-serif;">""",
        # Global gradients
        """
        <svg width="0" height="0" style="position:absolute">
          <defs>
            <linearGradient id="g1" x1="0" x2="1" y1="0" y2="1">
              <stop offset="0%" stop-color="#A5D6A7"/>
              <stop offset="100%" stop-color="#388E3C"/>
            </linearGradient>
            <linearGradient id="g2" x1="0" x2="1" y1="0" y2="1">
              <stop offset="0%" stop-color="#E8F5E9"/>
              <stop offset="100%" stop-color="#A5D6A7"/>
            </linearGradient>
          </defs>
        </svg>
        """
    ]

    POS_MAP = {
        "Top Left": (8, 8), "Top Center": (50, 8), "Top Right": (92, 8),
        "Center": (50, 50), "Bottom Left": (8, 92), "Bottom Center": (50, 92),
        "Bottom Right": (92, 92), "Left": (6, 50), "Right": (94, 50),
        "Top": (50, 6), "Bottom": (50, 94)
    }

    # -----------------------
    # Shapes
    # -----------------------
    for shape in shapes:
        s_type = shape.get("shape", "rectangle")
        s_pos = shape.get("position", "Center")
        s_size = shape.get("size", "40%")
        s_color = shape.get("color", "#FFFFFF")
        s_opacity = safe_float(shape.get("opacity", 0.9), 0.9)
        s_layer = shape.get("layer", "background")
        xperc, yperc = POS_MAP.get(s_pos, (50, 50))
        z_index = 0 if s_layer == "background" else 1

        w = h = s_size if "px" in str(s_size) else f"{safe_float(s_size, 40)}%"

        if s_type == "wave":
            pos_style = "bottom:0;" if "bottom" in s_pos.lower() else "top:0;"
            html_parts.append(f"""
            <svg viewBox="0 0 800 240" preserveAspectRatio="none"
                 style="position:absolute; left:10%; width:80%; height:40%; {pos_style}
                        z-index:{z_index}; opacity:{s_opacity};">
              <path d="M0,120 C200,40 400,200 800,120 L800,240 L0,240 Z" fill="{s_color}"/>
            </svg>""")
            continue

        border_radius = {"circle": "50%", "floral": "50%", "sticker": "20px"}.get(s_type, "15px")
        html_parts.append(f"""
        <div style="position:absolute; top:{yperc}%; left:{xperc}%;
                    width:{w}; height:{h}; background:{s_color};
                    opacity:{s_opacity}; border-radius:{border_radius};
                    box-shadow:0 12px 30px rgba(0,0,0,0.15);
                    z-index:{z_index};"></div>
        """)

    # Decorative overlay for premium depth
    html_parts.append("""
    <div style="position:absolute; inset:0; pointer-events:none;
                background: radial-gradient(60% 40% at 30% 20%, rgba(255,255,255,0.2), transparent 20%),
                            linear-gradient(180deg, rgba(0,0,0,0.02), transparent 40%);
                z-index:0;"></div>
    """)

    # -----------------------
    # Texts
    # -----------------------
    for idx, t in enumerate(texts):
        if isinstance(t, dict):
            content = t.get("content", "")
            font_style = t.get("font_style", "sans-serif")
            font_size = t.get("font_size", "40px")
            color = t.get("font_color", "#000000")
            angle = t.get("angle", "0deg")
            text_shape = t.get("text_shape", "straight")
            style_list = t.get("style", []) or []
            pos = t.get("position", "Center")
            layer = t.get("layer", "foreground")
        elif isinstance(t, str):
            content, font_style, font_size, color, angle = t, "sans-serif", "40px", "#000000", "0deg"
            text_shape, style_list, pos, layer = "straight", [], "Center", "foreground"
        else:
            continue

        xperc, yperc = POS_MAP.get(pos, (50, 50))
        z_index = 3 if layer == "foreground" else 1
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

        # Curved text
        if text_shape == "curved":
            try: fs = int(str(font_size).replace("px", ""))
            except: fs = 40
            radius = max(80, fs * 2 + 20)
            cx, cy = width_px * (xperc / 100), height_px * (yperc / 100)
            path_id = f"curve_path_{idx}"
            html_parts.append(f"""
            <svg style="position:absolute; left:0; top:0; width:{width_px}px; height:{height_px}px; z-index:{z_index}; pointer-events:none;">
              <defs><path id="{path_id}" d="M {cx-radius} {cy} A {radius} {radius} 0 0 1 {cx+radius} {cy}" /></defs>
              <text style="font-family:{font_style}; font-size:{font_size}; font-weight:{font_weight}; font-style:{font_style_css};">
                <textPath href="#{path_id}" startOffset="50%" text-anchor="middle" style="fill:{color}; text-shadow:{text_shadow_css};">
                  {content}
                </textPath>
              </text>
            </svg>
            """)
            continue

        # Sticker/CTA
        if "sticker" in style_list or content.strip().lower().startswith(("try", "book")):
            pill_w, pill_h = 160, 56
            left = f"calc({xperc}% - {pill_w/2}px)"
            top = f"calc({yperc}% - {pill_h/2}px)"
            html_parts.append(f"""
            <div style="position:absolute; left:{left}; top:{top}; width:{pill_w}px; height:{pill_h}px;
                        border-radius:{pill_h/2}px; display:flex; align-items:center; justify-content:center;
                        background:linear-gradient(90deg,#388E3C,#A5D6A7);
                        box-shadow:0 12px 35px rgba(56,142,60,0.25); z-index:{z_index};">
              <span style="font-family:{font_style}; font-size:{font_size}; font-weight:{font_weight}; color:#F8F4EA;">
                {content}
              </span>
            </div>
            """)
            continue

        # Standard straight text
        html_parts.append(f"""
        <div style="position:absolute; top:{yperc}%; left:{xperc}%;
                    transform:translate(-50%,-50%) rotate({angle});
                    font-family:{font_style}; font-size:{font_size}; font-weight:{font_weight};
                    font-style:{font_style_css}; {gradient_css}; text-shadow:{text_shadow_css};
                    z-index:{z_index}; text-align:center; white-space:nowrap;">
          {content}
        </div>
        """)

    # Glossy overlay for premium depth
    html_parts.append("""
    <div style="position:absolute; inset:0; border-radius:20px;
                box-shadow: inset 0 0 80px rgba(255,255,255,0.03),
                            inset 0 -30px 80px rgba(0,0,0,0.06);
                z-index:10; pointer-events:none;"></div>
    """)
    html_parts.append("</div>")

    return "\n".join(html_parts)


# ==========================================================
# HTML → Image Renderer
# ==========================================================
def display_HTML2Img(html_content: str, output_path="flyer_preview.png"):
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    hti = Html2Image(output_path=os.path.dirname(output_path) or ".", size=(1024, 768))
    hti.screenshot(html_str=html_content, save_as=os.path.basename(output_path))
    return output_path


# ==========================================================
# Theme Analyzer Node
# ==========================================================
def theme_analyzer_node(state: FlyerState) -> FlyerState:
    """Analyze theme, generate elegant flyer HTML, leave rendering/display to Streamlit."""

    user_prompt = state.user_prompt.strip()
    if not user_prompt:
        state.log("❌ Empty prompt. Skipping theme analysis.")
        state.html_output = "<p style='color:red;'>Empty prompt.</p>"
        return state

    llm = initialize_llm()
    state.log(f"⚙️ Using Gemini model for theme analysis: {getattr(llm, 'model', 'Unknown')}")
    llm_prompt = THEME_ANALYZER_PROMPT.replace("{user_prompt}", user_prompt)

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

        state.log("✅ Theme analysis completed successfully.")
        state.log("✅ Flyer HTML generated and stored in state.html_output.")

    except json.JSONDecodeError:
        err = "❌ Failed to decode JSON from Gemini output."
        state.log(err)
        state.theme_json = {"error": "Invalid JSON structure"}
        state.html_output = f"<p style='color:red;'>{err}</p>"

    except Exception as e:
        err = f"❌ Unexpected error during theme generation: {e}"
        state.log(err)
        state.theme_json = {"error": str(e)}
        state.html_output = f"<p style='color:red;'>{err}</p>"

    return state
