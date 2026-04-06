<<<<<<< HEAD
"""
models.py — Pydantic schemas for the Lifestyle Planner Environment.

Design principles:
- Observations carry full context an agent needs to act.
- Actions are structured (not free-text dumps) so graders can evaluate
  individual components independently.
- State tracks trajectory history, enabling multi-step episodes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Task types
# ---------------------------------------------------------------------------

TaskType = Literal["plan_day", "recover_day", "optimize_week"]


# ---------------------------------------------------------------------------
# Observation — what the agent sees at each step
# ---------------------------------------------------------------------------

class LifestyleObservation(BaseModel):
    """
    Full context delivered to the agent at each environment step.

    Fields:
        task_type   : which of the three tasks is active
        user_profile: stable facts about the user (sleep debt, energy, goals)
        context     : dynamic, step-specific information (time remaining,
                      missed tasks, feedback from previous step)
        step_index  : which step in the episode (0 = first look)
        instruction : natural-language prompt the agent should respond to
        feedback    : grader feedback from the previous step (empty on step 0)
    """

    task_type: TaskType
    user_profile: Dict[str, Any]
    context: Dict[str, Any]
    step_index: int = 0
    instruction: str
    feedback: Optional[str] = None  # populated from step 1 onward


# ---------------------------------------------------------------------------
# Action — structured response from the agent
# ---------------------------------------------------------------------------

class TimeBlock(BaseModel):
    """A single scheduled block in a day or week plan."""
    start: str = Field(..., description="Start time, e.g. '07:00'")
    end: str = Field(..., description="End time, e.g. '08:00'")
    activity: str = Field(..., description="What the user does in this block")
    priority: Literal["high", "medium", "low"] = "medium"
    rationale: Optional[str] = None  # why this block was scheduled here


class LifestyleAction(BaseModel):
    """
    Structured agent response.

    Rather than a single free-text blob, the agent must provide:
    - A short executive summary
    - An explicit schedule (list of time blocks)
    - Named strategies it is applying
    - An explicit self-evaluation with confidence

    This structure lets graders evaluate each dimension independently.
    """

    summary: str = Field(
        ...,
        description="One-paragraph executive summary of the plan.",
        max_length=400,
    )
    schedule: List[TimeBlock] = Field(
        ...,
        description="Ordered list of time blocks forming the plan.",
        min_length=2,
    )
    strategies: List[str] = Field(
        ...,
        description="Named strategies or principles applied (e.g. 'time-blocking', "
                    "'energy-matching', 'habit stacking').",
        min_length=1,
    )
    self_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Agent's own estimate of plan quality (calibration is graded).",
    )
    notes: Optional[str] = Field(
        None,
        description="Optional caveats, assumptions, or edge-case handling.",
    )


# ---------------------------------------------------------------------------
# State — internal environment state (returned by env.state())
# ---------------------------------------------------------------------------

class StepRecord(BaseModel):
    """Snapshot of a single completed step."""
    step_index: int
    action_summary: str
    grader_scores: Dict[str, float]   # per-rubric criterion scores
    total_score: float
    feedback: str


class LifestyleState(BaseModel):
    """
    Full episode state.

    Tracks the trajectory of an episode so reviewers and loggers can
    reconstruct exactly what happened.
    """

    episode_id: str
    task_type: TaskType
    difficulty: Literal["easy", "medium", "hard"]
    step_count: int = 0
    max_steps: int = 3
    cumulative_score: float = 0.0
    done: bool = False
    history: List[StepRecord] = Field(default_factory=list)
=======
from pydantic import BaseModel
from typing import List, Optional


class LifestyleTask(BaseModel):
    name: str
    priority: int
    duration: int
    deadline: int


class LifestyleObservation(BaseModel):
    current_time: int
    max_time: int
    energy_level: int
    tasks: List[LifestyleTask]
    completed_tasks: List[str]


class LifestyleState(BaseModel):
    current_time: int
    max_time: int
    energy_level: int
    tasks: List[LifestyleTask]
    completed_tasks: List[str]
    total_reward: float


class LifestyleAction(BaseModel):
    task_name: str


class StepResult(BaseModel):
    observation: LifestyleObservation
    reward: float
    done: bool
    info: dict
    
>>>>>>> 6d39c54215ae40124371e71bc5c5390de8d5fe7e
