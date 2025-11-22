import re, json, os
from core.state import FlyerState
from utils.prompt_utils import refinement_prompt
from models.llm_model import initialize_llm
from agents.image_agent import inject_images_for_preview, save_html

model = initialize_llm()

def refinement_node(state: FlyerState) -> FlyerState:
    state.log(f"[refinement_node] Iteration {state.iteration_count} — sending HTML to Gemini for review & edit.")

    # Prepare prompt
    prompt = refinement_prompt.replace("{html_final}", state.html_final)

    try:
        response = model.invoke(prompt)
        result_text = getattr(response, "content", str(response)).strip()

        # Extract JSON
        json_match = re.search(r"\{.*}", result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            state.evaluation_json = result

            # Get edited HTML or fallback to original
            edited = result.get("edited_html")
            if edited and len(edited) > 100:
                state.html_refined = edited
            else:
                state.html_refined = state.html_final
        else:
            state.evaluation_json = {"judgment": "Could not parse LLM output JSON."}
            state.html_refined = state.html_final

    except Exception as e:
        state.evaluation_json = {"judgment": f"Error: {e}"}
        state.html_refined = state.html_final
        state.log(f"❌ Refinement failed: {e}")

    state.iteration_count += 1
    state.log(
        f"Iteration {state.iteration_count} completed. Judgment: {state.evaluation_json.get('judgment', 'No judgment')}")

    # Save refined HTML
    if state.html_refined:
        refined_with_images = inject_images_for_preview(state.html_refined)
        output_path = save_html(state, filename="flyer_refined.html", html_attr=None, content_override=refined_with_images)
        state.log(f"💾 Refined HTML with images saved to: {output_path}")
    else:
        state.log("⚠️ No HTML to save after refinement.")

    return state
