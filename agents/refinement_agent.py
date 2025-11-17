"""
Refinement Agent
• Reviews flyer HTML using LLM and improves layout, text readability, and balance
• Ensures a fallback if refinement fails
• Prints results in Streamlit for easy inspection
"""

import re, json, os
from core.state import FlyerState
from utils.prompt_utils import refinement_prompt
from models.llm_model import initialize_llm
from core import config
import streamlit as st

MODEL_NAME = config.ACTIVE_MODEL
model = initialize_llm()

# -------------------------------
# Refinement Node
# -------------------------------
def refinement_node(state: FlyerState) -> FlyerState:
    state.log(f"[refinement_node] Iteration {state.iteration_count} — reviewing HTML flyer.")

    # Use html_final as input
    prompt = refinement_prompt.replace("{html_final}", state.html_final)

    try:
        # LLM generates review and edited HTML
        response = model.generate_content(prompt)
        result_text = getattr(response, "text", str(response)).strip()

        # Display raw LLM output in Streamlit
        st.text_area("🔹 LLM Refinement Output", result_text, height=200)

        # Extract JSON block
        json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            state.evaluation_json = result
            # Use edited_html if present, otherwise fallback to html_final
            state.html_refined = result.get("edited_html") or state.html_final
        else:
            # Fallback
            state.evaluation_json = {"judgment": "LLM output could not be parsed"}
            state.html_refined = state.html_final
            state.log("⚠️ Could not parse LLM JSON output. Using original HTML.")

    except Exception as e:
        state.evaluation_json = {"judgment": f"Error: {e}"}
        state.html_refined = state.html_final
        state.log(f"❌ Refinement failed: {e}")

    # Increment iteration
    state.iteration_count += 1
    state.log(f"Iteration {state.iteration_count} completed. Judgment: {state.evaluation_json.get('judgment', '')}")

    # Save refined HTML automatically
    if state.html_refined:
        output_path = save_refined_html(state)
        state.log(f"💾 Refined HTML saved to: {output_path}")
    else:
        state.log("⚠️ No HTML to save after refinement.")

    return state

# -------------------------------
# Save refined HTML
# -------------------------------
def save_refined_html(state: FlyerState, filename="flyer_refined.html") -> str:
    if not hasattr(state,"html_refined") or not state.html_refined:
        raise ValueError("No refined HTML found in state.html_refined")

    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    with open(filename,"w",encoding="utf-8") as f:
        f.write(state.html_refined)

    return os.path.abspath(filename)
