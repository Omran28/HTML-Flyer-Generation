def should_refine(state: FlyerState):
    feedback = getattr(state, "evaluation_json", {}).get("feedback", "")
    iteration = getattr(state, "iteration_count", 0)

    if not feedback or iteration >= 3:
        return "output"
    return "refine"



def evaluation_node(state: FlyerState) -> FlyerState:
    state.log("🔍 [evaluate_node] Placeholder — evaluation not implemented yet.")
    state.evaluation_json = {"feedback": "Looks good overall!"}
    return state