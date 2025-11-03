from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class FlyerState:
    # Input information
    user_prompt: str = ""          # The user's natural language request for the flyer
    api_provider: str = "gemini"   # The model or API backend used for generation

    # Intermediate stage outputs
    theme_json: Dict[str, Any] = field(default_factory=dict)        # Theme extraction output (colors, fonts, composition)
    text_json: Dict[str, Any] = field(default_factory=dict)         # Generated texts like title, subtitle, slogans
    image_json: Dict[str, Any] = field(default_factory=dict)        # Generated background and visual assets
    html_output: str = ""                                           # HTML layout composed of all assets
    evaluation_json: Dict[str, Any] = field(default_factory=dict)   # Evaluation results for refinement or scoring

    # Final outputs
    final_output: str = ""        # Final HTML flyer layout after refinement
    refined_html: str = ""        # HTML after images and refinement
    flyer_summary: str = ""       # Textual description of the generated flyer
    generated_images: List[str] = field(default_factory=list)  # Paths to generated images
    iteration_count: int = 1

    # Logging and metadata
    messages: List[str] = field(default_factory=list)    # Log of progress messages
    progress_log: str = ""                               # Combined progress string
    error: Optional[str] = None                          # Error message if any failure occurs
    needs_refinement: bool = False                       # Whether evaluation requests another refinement pass

    def log(self, message: str):
        # Append a status message to logs
        self.messages.append(message)

    def get(self, key: str, default: Any = None) -> Any:
        # Provide dict-like access for workflow compatibility
        return getattr(self, key, default)
