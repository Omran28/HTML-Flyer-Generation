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
            state.refined_html = result.get("edited_html", state.refined_html)
        else:
            state.evaluation_json = {"judgment": " Could not parse LLM output."}
    except Exception as e:
        state.evaluation_json = {"judgment": f" Error: {e}"}

    state.iteration_count += 1
    state.log(f" Iteration {state.iteration_count} completed. Judgment: {state.evaluation_json.get('judgment', '')}")
    
    # Display results
    save_refined_html(state)
    display(HTML("<h3>Enhanced Flyer (After LLM Edit)</h3>" + state.refined_html))

    return state



def save_refined_html(state):
    if not hasattr(state, "refined_html") or not state.refined_html:
        raise ValueError("No refined HTML found in state.refined_html")

    # Default file path
    output_path = "flyer_refined.html"

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Write the HTML
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(state.refined_html)

    return os.path.abspath(output_path)
