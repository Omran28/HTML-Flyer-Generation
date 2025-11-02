def refinement_node(state: FlyerState) -> FlyerState:
    state.log("🛠️ [refinement_node] Placeholder — refinement not implemented yet.")
    state.iteration_count = getattr(state, "iteration_count", 0) + 1
    return state