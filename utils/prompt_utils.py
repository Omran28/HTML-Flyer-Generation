THEME_ANALYZER_PROMPT = """
You are a world-class flyer designer AI. Analyze the user prompt below and produce a JSON describing a premium, catchy, elegant flyer.

User Prompt:
{user_prompt}

Requirements for JSON output:
- Output ONLY valid JSON with the exact top-level keys: "theme", "texts", "layout", "images".
- All keys are mandatory.
- Make the result rich, creative, and premium. Use elegant palettes, layered shapes, and expressive typography.

JSON Schema (fill values based on the user prompt; do not include example values here):

{
  "theme": {
    "summary": "1–2 sentences describing the flyer’s purpose, mood, and artistic direction.",
    "tone": "string – e.g., 'luxurious', 'fresh', 'organic', 'energetic', 'elegant'",
    "keywords": ["string list of descriptive ideas"],
    "theme_colors": ["#hex1", "#hex2", "#hex3"],
    "imagery_ideas": ["short creative image ideas supporting the theme visually"]
  },

  "texts": [
    {
      "content": "Exact text to appear on flyer",
      "font_style": "serif | sans-serif | script | display | brush",
      "font_size": "string (e.g., '72px')",
      "font_color": "#hex or gradient(...)",
      "angle": "string (e.g., '0deg', '-10deg')",
      "text_shape": "straight | curved | diagonal | wavy | circular",
      "style": ["bold", "italic", "shadow", "outline", "glow", "gradient", "emboss", "sticker"],
      "position": "Top Left | Top Center | Center | Bottom Right | coordinates (x%, y%)",
      "priority": "high | medium | low",
      "layer": "foreground | background | overlay"
    }
  ],

  "layout": {
    "background": {
      "color": "#hex",
      "texture": "gradient | paper | sky | abstract | metallic"
    },
    "layout_shapes": [
      {
        "shape": "circle | rectangle | banner | wave | floral | sticker | blob",
        "position": "Top | Center | Bottom | Left | Right | Top Left | Bottom Right",
        "size": "string (e.g., '60%', '200px')",
        "color": "#hex",
        "opacity": 0.5-1.0,
        "layer": "background | foreground"
      }
    ],
    "balance": "symmetrical | asymmetrical | diagonal | layered"
  },

  "images": [
    {
      "description": "Background image matching flyer theme (brief and renderable)",
      "position": "Background",
      "size": "100%"
    },
    {
      "description": "One image per shape (sticker, floral, wave or decorative element) placed above its shape",
      "position": "Match shape position",
      "size": "Match shape size"
    }
  ]
}

Constraints:
- Do not include any commentary. Return only JSON matching the schema.
- Ensure all position, layer, and size values are renderable (percentages or px).
  
Make the flyer design feel ultra-premium and visually striking, using:
- layered lighting (subtle highlights, soft shadows)
- golden or pearl gradients for accents
- slightly translucent overlapping shapes
- elegant curvature in composition (not flat)
- luxurious typography interplay (script + display mix)
- depth through shadowed layers and texture variation
"""


refinement_prompt = """
You are an expert visual designer and HTML flyer reviewer.

1️⃣ Critically evaluate this HTML flyer:
   - Layout quality, color harmony, font usage, balance, readability.
   - Give a short score from 0–10.

2️⃣ Then, if improvements are needed:
   - Directly modify the HTML flyer to improve it.
   - Keep the original structure and text intact.

3️⃣ Return JSON:
{{ "judgment": "<your review and score>", "edited_html": "<the improved HTML code>" }}

Here is the flyer HTML:
{final_output}
"""


DESCRIPTIVE_SUMMARY_PROMPT = """
You are a visual designer.

Task:
Summarize the flyer design in 1-2 sentences,
as if describing it to a client.

Focus on color mood, style, layout, and key content.
Avoid technical HTML words.

FLYER DATA:
{flyer_data_json}
"""
