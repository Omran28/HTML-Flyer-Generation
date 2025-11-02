import json, re
import imgkit
from core.state import FlyerState
from models.llm_model import initialize_llm
from utils.prompt_utils import THEME_ANALYZER_PROMPT

# Helper for position mapping
POS_MAP = {
    "Top Left": "top:10%; left:10%;",
    "Top Center": "top:10%; left:50%; transform:translateX(-50%);",
    "Top Right": "top:10%; right:10%;",
    "Center": "top:50%; left:50%; transform:translate(-50%, -50%);",
    "Bottom Left": "bottom:10%; left:10%;",
    "Bottom Center": "bottom:10%; left:50%; transform:translateX(-50%);",
    "Bottom Right": "bottom:10%; right:10%;",
    "Left": "top:50%; left:10%; transform:translateY(-50%);",
    "Right": "top:50%; right:10%; transform:translateY(-50%);",
    "Top": "top:10%; left:50%; transform:translateX(-50%);",
    "Bottom": "bottom:10%; left:50%; transform:translateX(-50%);"
}

def generate_flyer_html_old(parsed: dict) -> str:
    texts = parsed.get("texts", [])
    shapes = parsed.get("layout", {}).get("layout_shapes", [])
    images = parsed.get("images", [])

    # Background
    bg_color = parsed.get("layout", {}).get("background", {}).get("color", "#fff")
    bg_texture = parsed.get("layout", {}).get("background", {}).get("texture", "")
    bg_style = f"width:800px; height:600px; border-radius:20px; overflow:hidden; position:relative; background:{bg_color};"
    html = [f"<div style='{bg_style}'>"]

    # Render shapes
    for idx, shape in enumerate(shapes):
        shape_type = shape.get("shape", "rectangle")
        color = shape.get("color", "#ccc")
        size = shape.get("size", "100px")
        pos = shape.get("position", "Center")
        style = POS_MAP.get(pos, "top:50%; left:50%; transform:translate(-50%, -50%);")

        border_radius = {
            "circle": "50%",
            "sticker": "15px",
            "floral": "15px",
            "wave": "15px"
        }.get(shape_type, "15px")

        html.append(
            f"<div style='position:absolute; {style} width:{size}; height:{size}; "
            f"background:{color}; border-radius:{border_radius}; z-index:0;'></div>"
        )

        # Image placeholder above shape
        if idx+1 < len(images):
            img = images[idx+1]
            html.append(
                f"<!-- Image placeholder: {img.get('description','')} -->"
            )

    # Render texts
    for t in texts:
        x, y = (50, 50)
        pos = t.get("position", "Center")
        if pos in POS_MAP:
            # approximate percentage
            pos_coords = {
                "Top Left": (15, 15),
                "Top Center": (50, 15),
                "Top Right": (85, 15),
                "Center": (50, 50),
                "Bottom Left": (15, 85),
                "Bottom Center": (50, 85),
                "Bottom Right": (85, 85)
            }
            x, y = pos_coords.get(pos, (50,50))

        font = t.get("font_style", "sans-serif")
        size = t.get("font_size", "40px")
        color = t.get("font_color", "#000")
        angle = t.get("angle", "0deg")
        style_list = t.get("style", [])
        layer = t.get("layer", "foreground")

        font_weight = "bold" if "bold" in style_list else "normal"
        font_style_css = "italic" if "italic" in style_list else "normal"
        text_shadow = "2px 2px 8px rgba(0,0,0,0.4);" if "shadow" in style_list else ""

        html.append(
            f"<div style='position:absolute; top:{y}%; left:{x}%; transform:translate(-50%, -50%) rotate({angle}); "
            f"font-family:{font}; font-size:{size}; color:{color}; font-weight:{font_weight}; "
            f"font-style:{font_style_css}; text-shadow:{text_shadow}; "
            f"z-index:{1 if layer=='foreground' else 0}; text-align:center;'>{t.get('content','')}</div>"
        )

    html.append("</div>")
    return "\n".join(html)


def generate_flyer_html(parsed: dict) -> str:
    """
    Generate a premium, layered flyer HTML from LLM JSON.
    - parsed: dict from LLM containing keys: theme, texts, layout, images
    - Images are left as commented placeholders (uncomment and provide real src when available)
    """
    # Safely extract parts
    theme = parsed.get("theme", {})
    texts = parsed.get("texts", []) or []
    layout = parsed.get("layout", {}) or {}
    shapes = layout.get("layout_shapes", []) or []
    images = parsed.get("images", []) or []

    # Canvas size
    width_px = 800
    height_px = 600

    # Background
    bg_color = layout.get("background", {}).get("color", theme.get("theme_colors", ["#FFFFFF"])[0])
    bg_texture = layout.get("background", {}).get("texture", "")

    # Start HTML
    html_parts = []
    html_parts.append(f"""<div style="width:{width_px}px; height:{height_px}px; border-radius:20px; overflow:hidden;
                          position:relative; background:{bg_color}; font-family:sans-serif;">""")

    # Inline defs: gradient ids for dynamic gradients
    html_parts.append("""
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
    """)

    # Helper to map position to CSS
    POS_MAP = {
        "Top Left": "top:8%; left:8%; transform:none;",
        "Top Center": "top:8%; left:50%; transform:translateX(-50%);",
        "Top Right": "top:8%; right:8%; transform:none;",
        "Center": "top:50%; left:50%; transform:translate(-50%,-50%);",
        "Bottom Left": "bottom:8%; left:8%; transform:none;",
        "Bottom Center": "bottom:8%; left:50%; transform:translateX(-50%);",
        "Bottom Right": "bottom:8%; right:8%; transform:none;",
        "Left": "top:50%; left:6%; transform:translateY(-50%);",
        "Right": "top:50%; right:6%; transform:translateY(-50%);",
        "Top": "top:6%; left:50%; transform:translateX(-50%);",
        "Bottom": "bottom:6%; left:50%; transform:translateX(-50%);"
    }

    # Render shapes with some premium styles (SVG wave + blobs)
    for i, shape in enumerate(shapes):
        s_type = shape.get("shape", "rectangle")
        s_pos = shape.get("position", "Center")
        s_size = shape.get("size", "40%")  # may be "60%" etc.
        s_color = shape.get("color", "#FFFFFF")
        s_opacity = shape.get("opacity", 0.9) if isinstance(shape.get("opacity", None), (int,float)) else 0.9
        s_layer = shape.get("layer", "background")

        css_pos = POS_MAP.get(s_pos, "top:50%; left:50%; transform:translate(-50%,-50%);")

        # convert percentage sizes to width/height CSS: assume square for simplicity if % given
        if isinstance(s_size, str) and s_size.endswith("%"):
            percent = float(s_size.strip("%"))
            w = f"{percent}%"  # relative to flyer width
            h = f"{percent}%"  # relative to flyer height
        else:
            # if px or other string, use as-is for both width/height
            w = s_size
            h = s_size

        # Special handling for wave shape (SVG)
        if s_type == "wave":
            # Use an SVG wave anchored at bottom/top depending on position
            if s_pos.lower().startswith("bottom"):
                wave_style = f"position:absolute; left:10%; bottom:0; width:80%; height:40%; z-index:0; opacity:{s_opacity};"
                html_parts.append(f"""
                <svg viewBox="0 0 800 240" preserveAspectRatio="none"
                     style="{wave_style}">
                  <path d="M0,120 C200,200 400,40 800,120 L800,240 L0,240 Z"
                        fill="{s_color}" />
                </svg>
                """)
            else:
                # top wave
                wave_style = f"position:absolute; left:10%; top:0; width:80%; height:40%; z-index:0; opacity:{s_opacity};"
                html_parts.append(f"""
                <svg viewBox="0 0 800 240" preserveAspectRatio="none" style="{wave_style}">
                  <path d="M0,120 C200,40 400,200 800,120 L800,0 L0,0 Z" fill="{s_color}"/>
                </svg>
                """)
            # placeholder for image above wave
            if i+1 < len(images):
                img_desc = images[i+1].get("description","")
                html_parts.append(f"<!-- Placeholder image for wave: {img_desc} -->")
            continue

        # Floral/blob/sticker/circle rendering
        border_radius = "15px"
        if s_type == "circle":
            border_radius = "50%"
        elif s_type == "floral":
            # bigger blob with lower opacity
            border_radius = "50%"
        elif s_type == "sticker":
            border_radius = "20px"

        html_parts.append(f"""
        <div style="position:absolute; {css_pos} width:{w}; height:{h};
                    background:{s_color}; opacity:{s_opacity};
                    border-radius:{border_radius}; box-shadow: 0 12px 30px rgba(0,0,0,0.12);
                    z-index:{0 if s_layer=='background' else 1};"></div>
        """)
        # placeholder for image on the shape
        if i+1 < len(images):
            img_desc = images[i+1].get("description","")
            html_parts.append(f"<!-- Placeholder image for shape: {img_desc} -->")

    # Decorative overlay to add soft vignette / luxury feel
    html_parts.append(f"""
      <div style="position:absolute; inset:0; pointer-events:none;
                  background: radial-gradient(60% 40% at 30% 20%, rgba(255,255,255,0.2), transparent 20%),
                              linear-gradient(180deg, rgba(0,0,0,0.02), transparent 40%); z-index:0;"></div>
    """)

    # Render texts (support gradient text, glow, multi-shadow, curved text via SVG)
    for idx, t in enumerate(texts):
        content = t.get("content", "")
        font_style = t.get("font_style", "sans-serif")
        font_size = t.get("font_size", "40px")
        color = t.get("font_color", "#000000")
        angle = t.get("angle", "0deg")
        text_shape = t.get("text_shape", "straight")
        style_list = t.get("style", []) or []
        pos = t.get("position", "Center")
        layer = t.get("layer", "foreground")

        # map position to coords
        POS_COORDS = {
            "Top Left": (15,15),
            "Top Center": (50,15),
            "Top Right": (85,15),
            "Center": (50,50),
            "Bottom Left": (15,85),
            "Bottom Center": (50,85),
            "Bottom Right": (85,85)
        }
        xperc, yperc = POS_COORDS.get(pos, (50,50))

        # build text effects
        font_weight = "700" if "bold" in style_list else "400"
        font_style_css = "italic" if "italic" in style_list else "normal"
        shadows = []
        if "shadow" in style_list:
            shadows.append("2px 4px 10px rgba(0,0,0,0.35)")
        if "glow" in style_list:
            shadows.append("0 0 10px rgba(255,255,255,0.35)")
        text_shadow_css = ", ".join(shadows) if shadows else "none"

        # gradient text support: if style contains 'gradient' or color contains 'gradient('
        use_gradient = ("gradient" in style_list) or ("gradient(" in str(color))
        gradient_css = ""
        if use_gradient:
            # use linear gradient overlay via background-clip
            gradient_css = ("background: linear-gradient(90deg, #388E3C, #A5D6A7); "
                            "-webkit-background-clip: text; color: transparent;")
            color_css = ""  # already handled
        else:
            gradient_css = f"color:{color};"

        # curved text -> use SVG circle/textPath centered at xperc,yperc
        if text_shape == "curved":
            # radius derived from font-size and desired curve; converting 'px' string to int fallback
            try:
                fs = int(str(font_size).replace("px",""))
            except:
                fs = 40
            radius = max(80, fs * 2 + 20)
            cx = width_px * (xperc/100)
            cy = height_px * (yperc/100)
            path_id = f"curve_path_{idx}"
            # create an arc path (semi-circle)
            start_x = cx - radius
            start_y = cy
            end_x = cx + radius
            end_y = cy
            # simple arc path (semi circle above center)
            svg_arc = f"""<svg style="position:absolute; left:0; top:0; width:{width_px}px; height:{height_px}px; z-index:{3 if layer=='foreground' else 1}; pointer-events:none;">
                <defs>
                  <path id="{path_id}" d="M {start_x} {start_y} A {radius} {radius} 0 0 1 {end_x} {end_y}" />
                </defs>
                <text style="font-family:{font_style}; font-size:{font_size}; font-weight:{font_weight}; font-style:{font_style_css};">
                  <textPath href="#{path_id}" startOffset="50%" text-anchor="middle" style="fill:{color}; text-shadow:{text_shadow_css};">
                    {content}
                  </textPath>
                </text>
              </svg>"""
            html_parts.append(svg_arc)
            continue

        # sticker CTA special style detection
        is_sticker_like = "sticker" in style_list or (content.strip().lower().startswith("try") or content.strip().lower().startswith("book"))

        if is_sticker_like:
            # Create pill CTA
            pill_w = 160
            pill_h = 56
            left = f"calc({xperc}% - {pill_w/2}px)"
            top = f"calc({yperc}% - {pill_h/2}px)"
            pill_html = f"""
            <div style="position:absolute; left:{left}; top:{top}; width:{pill_w}px; height:{pill_h}px;
                        border-radius:{pill_h/2}px; display:flex; align-items:center; justify-content:center;
                        background:linear-gradient(90deg,#388E3C,#A5D6A7); box-shadow:0 10px 30px rgba(56,142,60,0.25);
                        z-index:{3 if layer=='foreground' else 1};">
              <span style="font-family:{font_style}; font-size:{font_size}; font-weight:{font_weight}; color:#F8F4EA;">
                {content}
              </span>
            </div>
            """
            html_parts.append(pill_html)
            continue

        # Normal text block (supports gradient via gradient_css)
        # Add slight transform rotate(angle) and z-index by layer
        html_parts.append(f"""
        <div style="position:absolute; top:{yperc}%; left:{xperc}%;
                    transform:translate(-50%,-50%) rotate({angle});
                    font-family:{font_style}; font-size:{font_size}; font-weight:{font_weight}; font-style:{font_style_css};
                    {gradient_css} text-shadow:{text_shadow_css}; z-index:{3 if layer=='foreground' else 1};
                    text-align:center; white-space:nowrap;">
          {content}
        </div>
        """)

    # Add final soft vignette and border
    html_parts.append("""
      <div style="position:absolute; inset:0; border-radius:20px; box-shadow: inset 0 0 80px rgba(255,255,255,0.03), inset 0 -30px 80px rgba(0,0,0,0.06); z-index:10; pointer-events:none;"></div>
    """)

    html_parts.append("</div>")  # end canvas

    return "\n".join(html_parts)



def render_html_to_image(html_content: str, output_path: str = "flyer_preview.png") -> str:
    options = {
        "format": "png",
        "quality": "100",
        "encoding": "UTF-8",
        "enable-local-file-access": None,
        "width": 800,
        "height": 600,
        "disable-smart-width": ""
    }
    imgkit.from_string(html_content, output_path, options=options)
    return output_path


def theme_analyzer_node(state: FlyerState) -> FlyerState:
    user_prompt = state.user_prompt.strip()
    if not user_prompt:
        state.log("❌ Empty prompt")
        return state

    llm = initialize_llm()
    state.log("Invoking Gemini model for theme analysis...")

    try:
        llm_prompt = THEME_ANALYZER_PROMPT.replace("{user_prompt}", user_prompt)
        response = llm.invoke(llm_prompt)
        raw_output = getattr(response, "content", str(response)).strip()

        # Remove code blocks
        cleaned = re.sub(r"^```(?:json)?|```$", "", raw_output.strip(), flags=re.MULTILINE).strip()
        parsed = json.loads(cleaned)

        # Ensure all required keys exist
        REQUIRED_KEYS = ["theme", "texts", "layout", "images"]
        missing = [k for k in REQUIRED_KEYS if k not in parsed]
        if missing:
            raise ValueError(f"Missing keys in LLM output: {missing}")

        state.theme_json = parsed
        state.final_output = generate_flyer_html(parsed)
        state.log("✅ Flyer HTML generated successfully.")

    except Exception as e:
        err = f"❌ Unexpected error: {e}"
        print(err)
        state.log(err)
        state.final_output = f"<p style='color:red;'>{err}</p>"
        state.theme_json = {"error": str(e)}

    return state
