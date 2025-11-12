import google.generativeai as genai
from IPython.display import HTML, display
import json, re
from utils.prompt_utils import refinement_prompt
from core import config
from models.llm_model import initialize_llm
from core.state import FlyerState
import os

MODEL_NAME = config.ACTIVE_MODEL
model = initialize_llm()


def refinement_node(state: FlyerState) -> FlyerState:
    state.log(f" [refinement_node] Iteration {state.iteration_count} — sending HTML to Gemini for review & edit.")

    prompt = refinement_prompt.replace("{html_final}", state.html_final)
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        json_match = re.search(r"\{.*}", result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            state.evaluation_json = result
            state.html_refined = result.get("edited_html", state.html_final)
        else:
            state.evaluation_json = {"judgment": " Could not parse LLM output."}
            state.html_refined = state.html_final
    except Exception as e:
        state.evaluation_json = {"judgment": f" Error: {e}"}
        state.html_refined = state.html_final

    state.iteration_count += 1
    state.log(f" Iteration {state.iteration_count} completed. Judgment: {state.evaluation_json.get('judgment', '')}")

    # Save automatically if html_refined exists
    if state.html_refined:
        output_path = save_refined_html(state)
        state.log(f"💾 Refined HTML saved to: {output_path}")
    else:
        state.log("⚠️ No HTML to save after refinement.")

    return state



def save_refined_html(state):
    if not hasattr(state, "html_refined") or not state.html_refined:
        raise ValueError("No refined HTML found in state.html_refined")

    # Default file path
    output_path = "flyer_refined.html"

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Write the HTML
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(state.html_refined)

    return os.path.abspath(output_path)
