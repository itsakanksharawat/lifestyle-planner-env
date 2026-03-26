from pydantic import BaseModel, Field
from typing import Dict, Any


class LifestyleObservation(BaseModel):
    task_type: str
    user_state: Dict[str, Any]
    instruction: str


class LifestyleAction(BaseModel):
    action_type: str = Field(..., description="Type of action being taken")
    plan: str = Field(..., description="The agent's proposed lifestyle plan or strategy")


class LifestyleState(BaseModel):
    episode_id: str
    step_count: int
    task_type: str
    score: float = 0.0
    done: bool = False