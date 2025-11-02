"""Prompts file"""


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


IMAGE_PROMPT_GENERATOR = """
You are a visual designer crafting text prompts for image-generation models.

Based on the flyer theme and layout hints, generate prompts for:
- Main background image
- 2–3 decorative icons or stickers

Include:
- Composition
- Mood and tone
- Style matching the flyer theme
- Placement based on layout_shapes from theme JSON

Return JSON:
{
  "background_prompt": "short vivid prompt (max 30 words)",
  "stickers": ["list of sticker/icon ideas (1–3 items)"],
  "color_palette_hint": "describe lighting and color mood briefly"
}

FLYER CONTEXT:
{flyer_context_json}
"""


# HTML LAYOUT GENERATOR — combine texts, images, and layout
HTML_LAYOUT_GENERATOR = """
You are an expert web designer and HTML/CSS developer.

Task:
Generate a flyer layout in clean HTML with inline CSS.

Requirements:
- Use the provided flyer data, text JSON, image URLs, and layout shapes.
- Keep layout responsive and visually balanced.
- Do not include <html>, <head>, or <body> tags.
- Use inline CSS only.
- Reflect the tone and theme colors in styling.
- Prefer <div>, <h1>, <p>, <img> elements.

Output ONLY the HTML (no explanations or markdown).

FLYER DATA:
{flyer_data_json}
"""


# LAYOUT EVALUATOR — review HTML and suggest improvements
LAYOUT_EVALUATOR_PROMPT = """
You are a senior UI/UX designer reviewing a flyer’s HTML output.

Task:
- Identify layout, spacing, and readability issues.
- Suggest or apply small improvements (font sizes, alignment, colors).
- Do NOT change text meaning.

Return JSON:
{
  "feedback": ["list of issues or suggestions"],
  "revised_html": "string with improved layout if applicable"
}

HTML INPUT:
{html_code}
"""


# DESCRIPTIVE SUMMARY — summarize flyer design for clients
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
