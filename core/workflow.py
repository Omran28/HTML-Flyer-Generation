from langgraph.graph import StateGraph, END

from agents.image_agent import image_generator_node
from agents.refinement_agent import refinement_node
# --- MODIFIED ---
# Import the new assembler_node
from agents.theme_agent import theme_analyzer_node, assembler_node
from core.state import FlyerState


# Workflow builder
def create_workflow() -> StateGraph:
    workflow = StateGraph(FlyerState)

    # --- MODIFIED ---
    # We now have 4 nodes
    workflow.add_node("theme", theme_analyzer_node)
    workflow.add_node("image", image_generator_node)
    workflow.add_node("assemble", assembler_node) # <-- NEW NODE
    workflow.add_node("refine", refinement_node)

    # --- MODIFIED ---
    # This is the new, correct workflow
    workflow.set_entry_point("theme")
    workflow.add_edge("theme", "image")
    workflow.add_edge("image", "assemble")    # <-- NEW EDGE
    workflow.add_edge("assemble", "refine") # <-- NEW EDGE
    workflow.add_edge("refine", END)

    # workflow.add_edge("image", "refine") # <-- DELETE THIS OLD EDGE

    return workflow