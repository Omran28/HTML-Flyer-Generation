def generate_summary(flyer_json: dict) -> str:
    if not flyer_json:
        return "No flyer data available."

    theme = flyer_json.get("theme", {})
    texts = flyer_json.get("texts", [])
    layout = flyer_json.get("layout", {})

    # --- MODIFIED: Use .get() for safe access ---
    # This prevents KeyError if a text object is missing a "content" key

    title = texts[0].get("content", "Untitled Flyer") if texts else "Untitled Flyer"
    subtitle = texts[1].get("content", "") if len(texts) > 1 else ""

    # Tone
    tone = theme.get("tone", "neutral")

    # Key text content (this was already safe, good job)
    text_preview = ", ".join([t.get("content", "") for t in texts[:3]])

    # Layout elements (this was also safe)
    shapes = layout.get("layout_shapes", [])
    shapes_summary = ", ".join([s.get("shape", "") for s in shapes]) or "standard layout"

    return (
        f"The flyer titled '{title}' ({subtitle}) uses a {tone} tone. "
        f"Key content includes: {text_preview}. "
        f"Layout elements include: {shapes_summary}."
    )