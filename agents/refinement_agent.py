import re, json
from core.state import FlyerState
from utils.helpers import inject_images_for_preview, get_position_coordinates, save_html
from models.llm_model import initialize_llm
from utils.prompt_utils import refinement_prompt

model = initialize_llm()

def build_images_metadata(state: FlyerState) -> str:
    metadata = []
    for idx, img in enumerate(getattr(state, "generated_images", [])):
        metadata.append(f"{idx}: {img['path']} — pos:{img['pos']}, size:{img['size']}, layer:{img['layer']}")
    return "\n".join(metadata)

def refinement_node(state: FlyerState) -> FlyerState:
    state.log(f"[refinement_node] Iteration {state.iteration_count} — sending HTML and images to LLM for review.")
    images_meta_str = build_images_metadata(state)
    prompt = refinement_prompt.replace("{html_final}", state.html_final)
    prompt += f"\n\nImages:\n{images_meta_str}\nRefine HTML to harmonize text & images. Keep all images, respect positions/layers."

    try:
        response = model.invoke(prompt)
        result_text = getattr(response, "content", str(response)).strip()
        json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            state.evaluation_json = result
            refined_html = result.get("edited_html")
            state.html_refined = refined_html if refined_html and len(refined_html)>100 else state.html_final
        else:
            state.evaluation_json = {"judgment":"Could not parse LLM JSON."}
            state.html_refined = state.html_final
    except Exception as e:
        state.evaluation_json = {"judgment": f"Error: {e}"}
        state.html_refined = state.html_final
        state.log(f"❌ Refinement failed: {e}")

    # Inject images
    if state.html_refined and getattr(state, "generated_images", None):
        html = state.html_refined
        for idx, img in enumerate(state.generated_images):
            x, y = get_position_coordinates(img.get("pos","center"))
            z_index = 0 if img.get("layer","foreground")=="background" else 2
            size = parse_size(img.get("size","40%"))
            img_tag = f'<img src="{img["path"]}" style="position:absolute;top:{y}%;left:{x}%;width:{size};height:{size};transform:translate(-50%,-50%);z-index:{z_index};pointer-events:none;border-radius:10px;object-fit:cover;"/>'
            placeholder = f"<!-- IMAGE_{idx} -->"
            html = html.replace(placeholder, img_tag) if placeholder in html else html + img_tag

        state.html_refined = html
        preview_html = inject_images_for_preview(html)
        save_path = save_html(preview_html, filename="flyer_refined.html")
        state.log(f"💾 Refined HTML saved: {save_path}")

    state.iteration_count += 1
    return state
