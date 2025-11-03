from langgraph.graph import StateGraph, END
from core.state import FlyerState
from agents.theme_agent import theme_analyzer_node
from agents.image_agent import image_generator_node
from agents.refinement_agent import refinement_node


# Workflow builder
def create_workflow() -> StateGraph:
    workflow = StateGraph(FlyerState)

    workflow.add_node("theme", theme_analyzer_node)
    workflow.add_node("image", image_generator_node)
    workflow.add_node("refine", refinement_node)

    workflow.set_entry_point("theme")
    workflow.add_edge("theme", "image")
    workflow.add_edge("image", "refine")
    workflow.add_edge("refine", END)

    return workflow
