# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class ProjectSettings(BaseModel):
    """
    Global Truth Anchor - addresses the LLM hallucination problem
    These settings are forcibly injected into the generation prompt of every Shot
    """

    # Location Lock
    location_lock: Optional[str] = Field(
        None,
        description="Forced geographic constraint, overriding the model's associative bias. E.g.: 'Long Island, New York, USA (NOT Italy/Sicily)'"
    )

    # Negative Constraints
    negative_constraints: List[str] = Field(
        default_factory=list,
        description="List of forbidden elements. E.g.: ['Mediterranean architecture', 'olive trees', 'stone villages']"
    )

    # Style Lock
    style_overrides: Dict[str, str] = Field(
        default_factory=dict,
        description="Forcibly override specific visual attributes. E.g.: {'color_palette': 'American 1940s warm tones', 'architecture': 'New York suburban estates'}"
    )

    # Era Lock
    era_lock: Optional[str] = Field(
        None,
        description="Forced era constraint. E.g.: '1945 Post-WWII America'"
    )

    def to_prompt_injection(self) -> str:
        """
        Convert the settings into a string injectable into a prompt.
        This string is appended to the end of each Shot's t2i_prompt.
        """
        injections = []
        
        if self.location_lock:
            injections.append(f"LOCATION: {self.location_lock}")
        
        if self.negative_constraints:
            injections.append(f"EXCLUDE: {', '.join(self.negative_constraints)}")
        
        if self.style_overrides:
            for key, value in self.style_overrides.items():
                injections.append(f"{key.upper()}: {value}")
        
        if self.era_lock:
            injections.append(f"ERA: {self.era_lock}")
        
        return " | ".join(injections) if injections else ""

