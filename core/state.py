from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class FlyerState:
    # Input information
    user_prompt: str = ""
    api_provider: str = "gemini"

    theme_json: Dict[str, Any] = field(default_factory=dict)
    html_output: str = ""
    html_final: str = ""
    html_refined: str = ""
    flyer_summary: str = ""
    evaluation_json: Dict[str, Any] = field(default_factory=dict)
    generated_images: List[str] = field(default_factory=list)
    iteration_count: int = 1

    # Logging and metadata
    messages: List[str] = field(default_factory=list)
    progress_log: str = ""
    error: Optional[str] = None
    needs_refinement: bool = False

    def log(self, message: str):
        # Append a status message to logs
        self.messages.append(message)

    def get(self, key: str, default: Any = None) -> Any:
        # Provide dict-like access for workflow compatibility
        return getattr(self, key, default)
