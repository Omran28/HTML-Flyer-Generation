import re
import json
from core.state import FlyerState
from models.llm_model import initialize_llm
from utils.prompt_utils import THEME_ANALYZER_PROMPT
from utils.helpers import get_position_coordinates, safe_float, get_valid_color

# -------------------------------
# HTML Generator
# -------------------------------
def generate_flyer_html(parsed: dict) -> str:
    theme = parsed.get("theme", {})
    texts = parsed.get("texts", [])
    shapes = parsed.get("layout", {}).get("layout_shapes", [])
    width_px, height_px = 800,600
    bg_color = parsed.get("layout", {}).get("background", {}).get(
        "color", theme.get("theme_colors", ["#F8FBF8"])[0]
    )

    html_parts = [f'<div style="width:{width_px}px;height:{height_px}px;'
                  f'border-radius:20px;overflow:hidden;position:relative;'
                  f'background:{bg_color};font-family:sans-serif;">']

    # Shapes
    for shape in shapes:
        s_type = shape.get("shape","rectangle")
        x,y = get_position_coordinates(shape.get("position","center"))
        s_size = shape.get("size","40%")
        w = h = s_size if "%" in str(s_size) else f"{safe_float(s_size,40)}%"
        s_color = get_valid_color(shape.get("color","#FFFFFF"))
        opacity = min(safe_float(shape.get("opacity",0.9),0.9),0.6)
        border_radius = {"circle":"50%","floral":"50%","sticker":"20px"}.get(s_type,"15px")
        z_index = 0

        if s_type=="wave":
            pos_style = "bottom:0;" if "bottom" in str(shape.get("position","")).lower() else "top:0;"
            html_parts.append(f"""
            <svg viewBox="0 0 800 240" preserveAspectRatio="none"
                 style="position:absolute;left:10%;width:80%;height:40%;{pos_style}
                        z-index:{z_index};opacity:{opacity};">
              <path d="M0,120 C200,40 400,200 800,120 L800,240 L0,240 Z" fill="{s_color}"/>
            </svg>""")
            continue

        html_parts.append(f"""
        <div style="position:absolute;top:{y}%;left:{x}%;
                    width:{w};height:{h};background:{s_color};
                    opacity:{opacity};border-radius:{border_radius};
                    box-shadow:0 12px 30px rgba(0,0,0,0.15);
                    transform:translate(-50%,-50%);
                    z-index:{z_index};"></div>
        """)

    # Text layers
    for t in texts:
        content = t.get("content","")
        font_family = t.get("font_style","sans-serif")
        font_size = t.get("font_size","40px")
        color = get_valid_color(t.get("font_color","#000000"))
        angle = t.get("angle","0deg")
        style_list = t.get("style",[]) or []
        x,y = get_position_coordinates(t.get("position","center"))
        font_weight = "700" if "bold" in style_list else "400"
        font_style_css = "italic" if "italic" in style_list else "normal"
        shadows=[]
        if "shadow" in style_list: shadows.append("2px 4px 12px rgba(0,0,0,0.35)")
        if "glow" in style_list: shadows.append("0 0 12px rgba(255,255,255,0.35)")
        text_shadow_css = ", ".join(shadows) if shadows else "none"
        gradient_css = ("background: linear-gradient(90deg,#388E3C,#A5D6A7);"
                        "-webkit-background-clip:text;color:transparent;"
                        if "gradient" in style_list or "gradient(" in str(color) else f"color:{color};")
        z_index = 3

        html_parts.append(f"""
        <div style="position:absolute;top:{y}%;left:{x}%;
                    transform:translate(-50%,-50%) rotate({angle});
                    font-family:{font_family};font-size:{font_size};
                    font-weight:{font_weight};font-style:{font_style_css};
                    {gradient_css};text-shadow:{text_shadow_css};
                    z-index:{z_index};text-align:center;white-space:nowrap;">
          {content}
        </div>
        """)

    html_parts.append("<!-- IMAGE_PLACEHOLDER -->")
    html_parts.append("""<div style="position:absolute;inset:0;border-radius:20px;
                box-shadow:inset 0 0 20px rgba(0,0,0,0.05),
                            inset 0 -20px 40px rgba(0,0,0,0.08);
                z-index:10;pointer-events:none;"></div>""")
    html_parts.append("</div>")
    return "\n".join(html_parts)

# -------------------------------
# Theme Analyzer Node
# -------------------------------
def theme_analyzer_node(state: FlyerState) -> FlyerState:
    prompt_text = state.user_prompt.strip()
    if not prompt_text:
        state.log("❌ Empty prompt. Skipping theme analysis.")
        state.theme_json = {"error":"Empty prompt."}
        return state

    llm = initialize_llm()
    llm_prompt = THEME_ANALYZER_PROMPT.replace("{user_prompt}", prompt_text)
    state.log("⚙️ Running theme analysis with LLM...")

    try:
        response = llm.invoke(llm_prompt)
        raw_content = getattr(response, "content", str(response)).strip()
        cleaned = re.sub(r"^```(?:json)?|```$","",raw_content,flags=re.MULTILINE)
        parsed = json.loads(cleaned)
        required_keys = ["theme","texts","layout","images"]
        missing = [k for k in required_keys if k not in parsed]
        if missing: raise ValueError(f"Missing keys in LLM output: {missing}")
        state.theme_json = parsed
        state.html_output = generate_flyer_html(parsed)
        state.log("✅ Theme analysis complete. HTML generated with image placeholder.")
    except Exception as e:
        state.log(f"❌ Error during theme analysis: {e}")
        state.theme_json = {"error":str(e)}
        state.html_output = "<p style='color:red'>Error generating flyer theme.</p>"

    return state
