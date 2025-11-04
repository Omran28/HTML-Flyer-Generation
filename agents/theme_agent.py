import json, re
from core.state import FlyerState
from models.llm_model import initialize_llm
from utils.prompt_utils import THEME_ANALYZER_PROMPT
import os
import streamlit as st
from html2image import Html2Image


def generate_flyer_html(parsed: dict) -> str:

    # Safely extract all parts
    theme = parsed.get("theme", {})
    texts = parsed.get("texts", []) or []
    layout = parsed.get("layout", {}) or {}
    shapes = layout.get("layout_shapes", []) or []
    # images = parsed.get("images", []) or []

    width_px, height_px = 800, 600  # Canvas dimensions

    # Background
    bg_color = layout.get("background", {}).get("color", theme.get("theme_colors", ["#FFFFFF"])[0])

    # Start HTML container
    html_parts = [f"""<div style="width:{width_px}px; height:{height_px}px; border-radius:20px; overflow:hidden;
                        position:relative; background:{bg_color}; font-family:sans-serif;">""", """
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
    """]

    # Inline SVG gradient defs

    # Position mappings for CSS
    POS_MAP = {
        "Top Left": (8, 8),
        "Top Center": (50, 8),
        "Top Right": (92, 8),
        "Center": (50, 50),
        "Bottom Left": (8, 92),
        "Bottom Center": (50, 92),
        "Bottom Right": (92, 92),
        "Left": (6, 50),
        "Right": (94, 50),
        "Top": (50, 6),
        "Bottom": (50, 94)
    }

    # --- Render Shapes ---
    for i, shape in enumerate(shapes):
        s_type = shape.get("shape", "rectangle")
        s_pos = shape.get("position", "Center")
        s_size = shape.get("size", "40%")
        s_color = shape.get("color", "#FFFFFF")
        s_opacity = float(shape.get("opacity", 0.9))
        s_layer = shape.get("layer", "background")
        xperc, yperc = POS_MAP.get(s_pos, (50, 50))

        # Convert % sizes to CSS
        w = h = s_size if "px" in str(s_size) else f"{float(str(s_size).strip('%'))}%"

        z_index = 0 if s_layer == "background" else 1

        # Handle wave separately
        if s_type == "wave":
            position_style = "bottom:0;" if "bottom" in s_pos.lower() else "top:0;"
            html_parts.append(f"""
            <svg viewBox="0 0 800 240" preserveAspectRatio="none"
                 style="position:absolute; left:10%; width:80%; height:40%; {position_style} z-index:{z_index}; opacity:{s_opacity};">
              <path d="M0,120 C200,40 400,200 800,120 L800,240 L0,240 Z" fill="{s_color}"/>
            </svg>""")
            continue

        # Determine border-radius for shape type
        border_radius = {
            "circle": "50%",
            "floral": "50%",
            "sticker": "20px"
        }.get(s_type, "15px")

        html_parts.append(f"""
        <div style="position:absolute; top:{yperc}%; left:{xperc}%;
                    width:{w}; height:{h}; background:{s_color};
                    opacity:{s_opacity}; border-radius:{border_radius};
                    box-shadow:0 12px 30px rgba(0,0,0,0.12); z-index:{z_index};"></div>
        """)

    # --- Decorative overlay for luxury feel ---
    html_parts.append("""
    <div style="position:absolute; inset:0; pointer-events:none;
                background: radial-gradient(60% 40% at 30% 20%, rgba(255,255,255,0.2), transparent 20%),
                            linear-gradient(180deg, rgba(0,0,0,0.02), transparent 40%); z-index:0;"></div>
    """)

    # --- Render Texts ---
    for idx, t in enumerate(texts):
        # Support dict or string
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
            content = t
            font_style = "sans-serif"
            font_size = "40px"
            color = "#000000"
            angle = "0deg"
            text_shape = "straight"
            style_list = []
            pos = "Center"
            layer = "foreground"
        else:
            continue

        xperc, yperc = POS_MAP.get(pos, (50, 50))
        z_index = 3 if layer == "foreground" else 1
        font_weight = "700" if "bold" in style_list else "400"
        font_style_css = "italic" if "italic" in style_list else "normal"

        # Text shadows
        shadows = []
        if "shadow" in style_list: shadows.append("2px 4px 10px rgba(0,0,0,0.35)")
        if "glow" in style_list: shadows.append("0 0 10px rgba(255,255,255,0.35)")
        text_shadow_css = ", ".join(shadows) if shadows else "none"

        # Gradient text
        if "gradient" in style_list or "gradient(" in str(color):
            gradient_css = ("background: linear-gradient(90deg, #388E3C, #A5D6A7);"
                            "-webkit-background-clip: text; color: transparent;")
        else:
            gradient_css = f"color:{color};"

        # Curved text using SVG path
        if text_shape == "curved":
            try: fs = int(str(font_size).replace("px", ""))
            except: fs = 40
            radius = max(80, fs * 2 + 20)
            cx = width_px * (xperc / 100)
            cy = height_px * (yperc / 100)
            path_id = f"curve_path_{idx}"
            start_x, start_y = cx - radius, cy
            end_x, end_y = cx + radius, cy
            html_parts.append(f"""
            <svg style="position:absolute; left:0; top:0; width:{width_px}px; height:{height_px}px; z-index:{z_index}; pointer-events:none;">
              <defs><path id="{path_id}" d="M {start_x} {start_y} A {radius} {radius} 0 0 1 {end_x} {end_y}" /></defs>
              <text style="font-family:{font_style}; font-size:{font_size}; font-weight:{font_weight}; font-style:{font_style_css};">
                <textPath href="#{path_id}" startOffset="50%" text-anchor="middle" style="fill:{color}; text-shadow:{text_shadow_css};">
                  {content}
                </textPath>
              </text>
            </svg>
            """)
            continue

        # Sticker / CTA style
        is_sticker_like = "sticker" in style_list or content.strip().lower().startswith(("try", "book"))
        if is_sticker_like:
            pill_w, pill_h = 160, 56
            left = f"calc({xperc}% - {pill_w/2}px)"
            top = f"calc({yperc}% - {pill_h/2}px)"
            html_parts.append(f"""
            <div style="position:absolute; left:{left}; top:{top}; width:{pill_w}px; height:{pill_h}px;
                        border-radius:{pill_h/2}px; display:flex; align-items:center; justify-content:center;
                        background:linear-gradient(90deg,#388E3C,#A5D6A7); box-shadow:0 10px 30px rgba(56,142,60,0.25);
                        z-index:{z_index};">
              <span style="font-family:{font_style}; font-size:{font_size}; font-weight:{font_weight}; color:#F8F4EA;">
                {content}
              </span>
            </div>
            """)
            continue

        # Normal text
        html_parts.append(f"""
        <div style="position:absolute; top:{yperc}%; left:{xperc}%;
                    transform:translate(-50%,-50%) rotate({angle});
                    font-family:{font_style}; font-size:{font_size}; font-weight:{font_weight}; font-style:{font_style_css};
                    {gradient_css} text-shadow:{text_shadow_css}; z-index:{z_index};
                    text-align:center; white-space:nowrap;">
          {content}
        </div>
        """)

    # Final soft vignette / luxury overlay
    html_parts.append("""
    <div style="position:absolute; inset:0; border-radius:20px;
                box-shadow: inset 0 0 80px rgba(255,255,255,0.03), inset 0 -30px 80px rgba(0,0,0,0.06);
                z-index:10; pointer-events:none;"></div>
    """)

    html_parts.append("</div>")  # Close flyer container
    return "\n".join(html_parts)



def display_HTML2Img(html_content: str, output_path="flyer_html2Img.png") -> str:
    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        temp_html_path = "temp_flyer.html"
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Specify Colab Chromium path
        hti = Html2Image(browser_executable="/usr/bin/chromium-browser",
                          output_path=os.path.dirname(output_path) or ".")
        hti.screenshot(html_file=temp_html_path, save_as=os.path.basename(output_path))

        image_path = os.path.join(os.path.dirname(output_path), os.path.basename(output_path))
        return image_path

    except Exception as e:
        st.warning(f"⚠️ Failed to render HTML as image: {e}. Showing HTML preview instead.")
        # Fallback: just return None
        return None


def theme_analyzer_node(state: FlyerState) -> FlyerState:
    user_prompt = state.user_prompt.strip()
    if not user_prompt:
        state.log("❌ Empty prompt provided. Skipping theme analysis.")
        state.final_output = "<p style='color:red;'>Empty prompt.</p>"
        return state

    llm = initialize_llm()
    state.log(f"⚙️ Initialized Gemini model for theme analysis: {getattr(llm, 'model', 'Unknown')}")

    # Prepare prompt
    llm_prompt = THEME_ANALYZER_PROMPT.replace("{user_prompt}", user_prompt)
    state.log("🧠 Sending prompt to Gemini model...")

    try:
        response = llm.invoke(llm_prompt)

        # Handle object and string outputs
        raw_output = getattr(response, "content", str(response))
        raw_output = raw_output.strip()

        # Remove Markdown code fences and parse JSON
        cleaned = re.sub(r"^```(?:json)?|```$", "", raw_output, flags=re.MULTILINE)
        parsed = json.loads(cleaned)

        # Ensure all expected keys exist
        REQUIRED_KEYS = ["theme", "texts", "layout", "images"]
        missing = [k for k in REQUIRED_KEYS if k not in parsed]
        if missing:
            raise ValueError(f"Missing keys in LLM output: {missing}")

        # Save parsed JSON and HTML
        state.theme_json = parsed
        state.final_output = generate_flyer_html(parsed)

        state.log("✅ Theme analysis completed successfully.")
        state.log("✅ Flyer HTML generated and stored in state.final_output.")

    except json.JSONDecodeError:
        err_msg = "❌ Failed to decode JSON from Gemini output."
        state.log(err_msg)
        state.final_output = f"<p style='color:red;'>{err_msg}</p>"
        state.theme_json = {"error": "Invalid JSON structure"}

    except Exception as e:
        err_msg = f"❌ Unexpected error during theme generation: {e}"
        state.log(err_msg)
        state.final_output = f"<p style='color:red;'>{err_msg}</p>"
        state.theme_json = {"error": str(e)}

    return state
