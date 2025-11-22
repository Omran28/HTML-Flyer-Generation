import re, json
from core.state import FlyerState
from utils.helpers import inject_images_for_preview, get_position_coordinates, save_html, parse_size
from models.llm_model import initialize_llm
from utils.prompt_utils import refinement_prompt

model = initialize_llm()


def build_images_metadata(state: FlyerState) -> str:
    metadata = []
    # Include border_radius in the metadata sent to the LLM for context
    theme_images_meta = state.theme_json.get("images", [])

    for idx, img in enumerate(getattr(state, "generated_images", [])):
        # Try to get border_radius from the original theme JSON
        current_img_meta = theme_images_meta[idx] if idx < len(theme_images_meta) else {}
        radius = current_img_meta.get("border_radius", "10px")

        metadata.append(
            f"{idx}: {img['path']} — pos:{img['pos']}, size:{img['size']}, layer:{img['layer']}, radius:{radius}")
    return "\n".join(metadata)


def refinement_node(state: FlyerState) -> FlyerState:
    state.log(
        f"[refinement_node] Iteration {state.iteration_count} — sending HTML and images to LLM for high-end review.")
    images_meta_str = build_images_metadata(state)
    prompt = refinement_prompt.replace("{html_final}", state.html_final)

    # 💡 Send the structured image metadata for better LLM context
    prompt += f"\n\nImages (DO NOT change these assets):\n{images_meta_str}\n\nRefine HTML for optimal harmony, readability, and visual impact."

    try:
        response = model.invoke(prompt)
        result_text = getattr(response, "content", str(response)).strip()
        json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            state.evaluation_json = result
            refined_html = result.get("edited_html")
            state.html_refined = refined_html if refined_html and len(refined_html) > 100 else state.html_final
        else:
            state.evaluation_json = {"judgment": "Could not parse LLM JSON. Check LLM output format."}
            state.html_refined = state.html_final
    except Exception as e:
        state.evaluation_json = {"judgment": f"Critical LLM Error: {e}"}
        state.html_refined = state.html_final
        state.log(f"❌ Refinement failed: {e}")

    # Inject images
    if state.html_refined and getattr(state, "generated_images", None):
        html = state.html_refined
        theme_images_meta = state.theme_json.get("images", [])  # Get dynamic shape data

        for idx, img in enumerate(state.generated_images):
            x, y = get_position_coordinates(img.get("pos", "center"))
            z_index = 0 if img.get("layer", "foreground") == "background" else 2
            size = parse_size(img.get("size", "40%"))

            # 💡 FIX for Dynamic Shapes (Problem 1): Read the border_radius from theme_json
            current_img_meta = theme_images_meta[idx] if idx < len(theme_images_meta) else {}
            border_radius = current_img_meta.get("border_radius", "10px")  # Default is 10px

            # The z-index is set to 1 for the background image, and 2 for foreground images/shapes
            z_index = 1 if '100%' in str(size) and 'background' in img.get("layer", "").lower() else 2

            img_tag = f'<img src="{img["path"]}" style="position:absolute;top:{y}%;left:{x}%;width:{size};height:{size};transform:translate(-50%,-50%);z-index:{z_index};pointer-events:none;border-radius:{border_radius};object-fit:cover;"/>'
            placeholder = f""

            # Replace placeholder or append img tag if not found
            html = html.replace(placeholder, img_tag) if placeholder in html else html + img_tag

        state.html_refined = html
        preview_html = inject_images_for_preview(html)

        # 💡 FIX for File Saving (Problem 3): Use content_override
        save_path = save_html(state, filename="flyer_refined.html", content_override=preview_html)
        state.log(f"💾 Refined HTML saved: {save_path}")

    state.iteration_count += 1
    return state