import google.generativeai as genai
from IPython.display import HTML, display
import json, re
from utils.prompt_utils import refinement_prompt
from core import config
from models.llm_model import initialize_llm
from core.state import FlyerState

MODEL_NAME = config.ACTIVE_MODEL
model = initialize_llm()


def refinement_node(state: FlyerState) -> FlyerState:
    state.log(f" [refinement_node] Iteration {state.iteration_count} — sending HTML to Gemini for review & edit.")

    prompt = refinement_prompt.replace("{final_output}", state.final_output)
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
    display(HTML("<h3>Enhanced Flyer (After LLM Edit)</h3>" + state.html_code))

    return state