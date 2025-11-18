"""
agents/theme_agent.py
---------------------
Theme Analyzer Agent (Node 1 of 3)

• Analyzes user prompt to create the JSON plan.
• Generates the *Skeleton HTML* (Layout, Text, Shapes, Colors).
• CRITICAL: Sets correct z-indexes so shapes don't cover text.
"""

import os, re, json
from core.state import FlyerState
from models.llm_model import initialize_llm
from utils.prompt_utils import THEME_ANALYZER_PROMPT


# ==========================================================
# Utility: Robust Parsers
# ==========================================================
def safe_float(value, default=0.0):
    """Convert strings like '85%' or '100px' safely to float."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = (
            value.replace('%', '')
                 .replace('width', '')
                 .replace('height', '')
                 .replace(',', '')
                 .replace('px', '')
                 .split()[0]
                 .strip()
        )
        try:
            return float(cleaned)
        except ValueError:
            return default
    return default

def get_position(pos_str: str):
    """
    Smart position parser that handles 'custom(x,y)' and fuzzy text.
    Fixes the issue where text piles up in the center.
    """
    if not pos_str:
        return (50, 50)

    s = str(pos_str).lower().strip()

    # 1. Handle "custom (50%, 20%)" from your JSON
    if "custom" in s or "%" in s:
        try:
            # Extract all numbers (integers or floats)
            nums = re.findall(r"[\d\.]+", s)
            if len(nums) >= 2:
                # Return the first two numbers found as (x, y)
                return (float(nums[0]), float(nums[1]))
        except:
            pass # Fallback if parsing fails

    # 2. Fuzzy Matching for standard words
    if "top" in s and "left" in s: return (8, 8)
    if "top" in s and "right" in s: return (92, 8)
    if "top" in s and "center" in s: return (50, 8)

    if "bottom" in s and "left" in s: return (8, 92)
    if "bottom" in s and "right" in s: return (92, 92)
    if "bottom" in s and "center" in s: return (50, 92)

    if "center" in s: return (50, 50)

    # Edge centers
    if "left" in s: return (6, 50)
    if "right" in s: return (94, 50)
    if "top" in s: return (50, 6)
    if "bottom" in s: return (50, 94)

    # Default fallback
    return (50, 50)

def get_valid_color(color_str: str, default="#333333") -> str:
    """
    Ensures SVGs don't get CSS gradients in 'fill' attributes (which breaks them).
    If a gradient is detected, it extracts the first hex code as a fallback.
    """
    if not color_str: return default

    if "gradient" in str(color_str).lower():
        # Extract the first hex code found
        match = re.search(r"#[0-9a-fA-F]{6}", str(color_str))
        return match.group(0) if match else default

    return color_str


# ==========================================================
# HTML Generator (Skeleton Builder)
# ==========================================================
def generate_flyer_html(parsed: dict) -> str:
    """
    Generate the HTML Skeleton.
    Includes: Layout container, Background Color, Shapes, Text, Gradients.
    Excludes: Dynamic Images (The Image Agent will inject these later).
    """
    theme = parsed.get("theme", {})
    texts = parsed.get("texts", [])
    layout = parsed.get("layout", {})
    shapes = layout.get("layout_shapes", [])

    width_px, height_px = 800, 600

    # Base background color (Image Agent might overlay a real image later)
    bg_color = layout.get("background", {}).get("color", theme.get("theme_colors", ["#FFFFFF"])[0])

    html_parts = [
        f"""<div style="width:{width_px}px; height:{height_px}px; border-radius:20px; overflow:hidden;
                        position:relative; background:{bg_color}; font-family:sans-serif;">""",
        # Global gradients (Premium feel)
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

    # -----------------------
    # Shapes (Background Layer)
    # -----------------------
    for shape in shapes:
        s_type = shape.get("shape", "rectangle")
        s_pos = shape.get("position", "Center")
        s_size = shape.get("size", "40%")

        # Fix for SVG gradient issue
        s_color_raw = shape.get("color", "#FFFFFF")
        s_color = get_valid_color(s_color_raw)

        # Fix: Limit opacity so text is visible behind shapes
        s_opacity = min(safe_float(shape.get("opacity", 0.9), 0.9), 0.6)
        s_layer = shape.get("layer", "background")

        xperc, yperc = get_position(s_pos)

        # CRITICAL FIX: Z-Index 0 for shapes
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
        <div style="position:absolute; top:{yperc}%; left:{xperc}%;
                    width:{w}; height:{h}; background:{s_color};
                    opacity:{s_opacity}; border-radius:{border_radius};
                    box-shadow:0 12px 30px rgba(0,0,0,0.15);
                    transform:translate(-50%, -50%);
                    z-index:{z_index};"></div>
        """)

    # -----------------------
    # Texts (Foreground Layer)
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
        else:
            continue

        xperc, yperc = get_position(pos)

        # CRITICAL FIX: Z-Index 3 for Text (Always on top)
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
# Node 1: Theme Analyzer
# ==========================================================
def theme_analyzer_node(state: FlyerState) -> FlyerState:
    """
    Analyze theme, generate JSON plan, AND generate the HTML Skeleton.
    """

    user_prompt = state.user_prompt.strip()
    if not user_prompt:
        state.log("❌ Empty prompt. Skipping theme analysis.")
        state.theme_json = {"error": "Empty prompt."}
        return state

    llm = initialize_llm()
    state.log(f"⚙️ Using Gemini model for theme analysis.")
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

        # --- 3-NODE WORKFLOW SPECIFIC ---
        # We generate the HTML Skeleton here.
        # The Image Agent (Node 2) will take this output and inject images into it.
        state.html_output = generate_flyer_html(parsed)

        state.log("✅ Theme analysis completed. JSON plan & HTML skeleton generated.")

    except Exception as e:
        err = f"❌ Unexpected error during theme generation: {e}"
        state.log(err)
        state.theme_json = {"error": str(e)}
        state.html_output = "<p style='color:red'>Error generating flyer theme.</p>"

    return state