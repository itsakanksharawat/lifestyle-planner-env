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
    