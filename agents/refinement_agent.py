import google.generativeai as genai
from IPython.display import HTML, display
import json, re

genai.configure(api_key="AIzaSyBXYAZtscie4MxmnBPyfIIMlXRyalAirak")  
MODEL_NAME = "models/gemini-2.5-pro"
model = genai.GenerativeModel(MODEL_NAME)
-
class FlyerState:
    def __init__(self, html_code, iteration_count=0):
        self.html_code = html_code
        self.iteration_count = iteration_count
        self.evaluation_json = {}
        self.log_messages = []

    def log(self, message):
        self.log_messages.append(message)
        print(message)

def refinement_node(state: FlyerState) -> FlyerState:
    state.log(f" [refinement_node] Iteration {state.iteration_count + 1} — sending HTML to Gemini for review & edit.")

    prompt = f"""
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
{state.html_code}
"""
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            state.evaluation_json = result
            state.html_code = result.get("edited_html", state.html_code)
        else:
            state.evaluation_json = {"judgment": " Could not parse LLM output."}
    except Exception as e:
        state.evaluation_json = {"judgment": f" Error: {e}"}

    state.iteration_count += 1
    state.log(f" Iteration {state.iteration_count} completed. Judgment: {state.evaluation_json.get('judgment', '')}")
    
    # Display results (optional in Jupyter)
    display(HTML("<h3>Enhanced Flyer (After LLM Edit)</h3>" + state.html_code))

    return state

initial_html = """<div style="width:800px; height:600px; background:#E8F3D6;">Your flyer HTML here</div>"""
state = FlyerState(initial_html)

state = refinement_node(state)  # Run the refinement
