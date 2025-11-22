import re
import json
from core.state import FlyerState
from utils.helpers import inject_images_for_preview, get_position_coordinates, save_html
from models.llm_model import initialize_llm
from utils.prompt_utils import refinement_prompt

model = initialize_llm()

def build_images_metadata(state: FlyerState) -> str:
    metadata = []
    for idx, img_path in enumerate(getattr(state, "generated_images", [])):
        img_meta = state.theme_json.get("images", [{}])[idx] if idx < len(state.theme_json.get("images", [])) else {}
        pos = img_meta.get("position", "center")
        size = img_meta.get("size", "40%")
        layer = img_meta.get("layer", "foreground")
        metadata.append(f"{idx}: {img_path} — position: {pos}, size: {size}, layer: {layer}")
    return "\n".join(metadata)

def refinement_node(state: FlyerState) -> FlyerState:
    state.log(f"[refinement_node] Iteration {state.iteration_count} — sending HTML and images to LLM for review & edit.")
    images_meta_str = build_images_metadata(state)
    prompt = refinement_prompt.replace("{html_final}", state.html_final)
    prompt += f"\n\nThe flyer contains the following images:\n{images_meta_str}\n"
    prompt += "Refine the HTML so the text and design harmonize with these images. Do not remove images."

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
            state.evaluation_json = {"judgment": "Could not parse LLM output JSON."}
            state.html_refined = state.html_final
    except Exception as e:
        state.evaluation_json = {"judgment": f"Error: {e}"}
        state.html_refined = state.html_final
        state.log(f"❌ Refinement failed: {e}")

    state.iteration_count += 1
    state.log(f"Iteration {state.iteration_count} completed. Judgment: {state.evaluation_json.get('judgment', 'No judgment')}")

    # Inject images into placeholders
    if state.html_refined and getattr(state, "generated_images", None):
        html = state.html_refined
        for idx, img_path in enumerate(state.generated_images):
            img_meta = state.theme_json.get("images", [{}])[idx] if idx < len(state.theme_json.get("images", [])) else {}
            pos = img_meta.get("position", "center")
            size = img_meta.get("size", "40%")
            layer = img_meta.get("layer", "foreground")
            x, y = get_position_coordinates(pos)
            z_index = 0 if layer == "background" else 2
            dims = "width:100%; height:100%;" if layer == "background" else f"width:{size}; height:{size};"
            img_tag = f'<img src="{img_path}" style="position:absolute; top:{y}%; left:{x}%; {dims} transform:translate(-50%, -50%); z-index:{z_index}; pointer-events:none; border-radius:10px; object-fit:cover;"/>'
            placeholder = f"<!-- IMAGE_{idx} -->"
            html = html.replace(placeholder, img_tag) if placeholder in html else html + img_tag
        state.html_refined = html
        preview_html = inject_images_for_preview(state.html_refined)
        save_path = save_html(preview_html, filename="flyer_refined_preview.html")
        state.log(f"💾 Refined HTML with images saved to: {save_path}")
    else:
        state.log("⚠️ No images to process or no refined HTML available.")
    return state
