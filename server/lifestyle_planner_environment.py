<<<<<<< HEAD
"""
server/lifestyle_planner_environment.py — Core RL environment.

Design principles:
- Multi-step episodes (default 3 steps) give agents a chance to refine plans
  based on intermediate feedback, making this a genuine sequential decision task.
- Each step returns a new observation that includes grader feedback from the
  previous step. A good agent should improve across steps.
- Cumulative score is the average of per-step scores (encouraging sustained quality,
  not just getting lucky on the final step).
- The environment is stateless between episodes: all state lives in self._state
  and self._task, reset on every reset() call.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Tuple

from models import (
    LifestyleAction,
    LifestyleObservation,
    LifestyleState,
    StepRecord,
)
from task_bank import DifficultyLevel, Task, sample_task
from graders import grade_action


class LifestylePlannerEnvironment:
    """
    OpenEnv-compatible environment for lifestyle planning tasks.

    Episode flow:
        obs = env.reset()                        # step 0: first observation
        obs, reward, done, info = env.step(act)  # step 1
        obs, reward, done, info = env.step(act)  # step 2
        obs, reward, done, info = env.step(act)  # step 3 → done=True

    The observation at step N+1 includes feedback from step N, so the agent
    can iterate and improve its plan across steps within the same episode.
    """

    MAX_STEPS: int = 3

    def __init__(self) -> None:
        self._task: Task | None = None
        self._state: LifestyleState | None = None
        self._last_feedback: str = ""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(
        self,
        task_type: str | None = None,
        difficulty: DifficultyLevel | None = None,
    ) -> LifestyleObservation:
        """
        Start a new episode.

        Args:
            task_type  : pin task type or None for random
            difficulty : pin difficulty or None for random

        Returns:
            Initial observation (step 0, no feedback yet).
        """
        self._task = sample_task(task_type=task_type, difficulty=difficulty)
        self._last_feedback = ""
        self._state = LifestyleState(
            episode_id=str(uuid.uuid4()),
            task_type=self._task["task_type"],
            difficulty=self._task["difficulty"],
            step_count=0,
            max_steps=self.MAX_STEPS,
            cumulative_score=0.0,
            done=False,
            history=[],
        )
        return self._build_observation(step_index=0)

    def step(
        self, action: LifestyleAction
    ) -> Tuple[LifestyleObservation, float, bool, Dict[str, Any]]:
        """
        Advance the episode by one step.

        Args:
            action : structured LifestyleAction from the agent

        Returns:
            observation : next observation (with feedback if not done)
            reward      : step reward in [0, 1]
            done        : True when max steps reached
            info        : grading details for logging
        """
        if self._state is None or self._task is None:
            raise RuntimeError("Call reset() before step().")
        if self._state.done:
            raise RuntimeError("Episode is done. Call reset() to start a new one.")

        # --- Grade the action ---
        criterion_scores, step_score, feedback = grade_action(
            task_type=self._task["task_type"],
            action=action,
            task_input={
                "user_profile": self._task["user_profile"],
                "context": self._task["context"],
            },
            rubric=self._task["rubric"],
        )

        # --- Record step ---
        self._state.step_count += 1
        record = StepRecord(
            step_index=self._state.step_count,
            action_summary=action.summary[:200],
            grader_scores=criterion_scores,
            total_score=step_score,
            feedback=feedback,
        )
        self._state.history.append(record)

        # Cumulative score: running average across steps
        all_scores = [r.total_score for r in self._state.history]
        self._state.cumulative_score = round(sum(all_scores) / len(all_scores), 4)

        done = self._state.step_count >= self.MAX_STEPS
        self._state.done = done
        self._last_feedback = feedback

        # --- Build next observation ---
        if done:
            next_obs = self._build_observation(
                step_index=self._state.step_count,
                instruction="Episode complete. Final scores recorded.",
            )
        else:
            next_obs = self._build_observation(step_index=self._state.step_count)

        info: Dict[str, Any] = {
            "step_score":        step_score,
            "criterion_scores":  criterion_scores,
            "cumulative_score":  self._state.cumulative_score,
            "task_type":         self._task["task_type"],
            "difficulty":        self._task["difficulty"],
            "episode_id":        self._state.episode_id,
        }

        return next_obs, step_score, done, info

    def state(self) -> LifestyleState:
        """Return full episode state (trajectory history, scores, metadata)."""
        if self._state is None:
            raise RuntimeError("Call reset() first.")
        return self._state

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_observation(
        self,
        step_index: int,
        instruction: str | None = None,
    ) -> LifestyleObservation:
        assert self._task is not None

        if instruction is None:
            if step_index == 0:
                instruction = self._task["instruction"]
            else:
                instruction = (
                    f"Refine your plan based on the feedback above. "
                    f"Step {step_index}/{self.MAX_STEPS}."
                )

        return LifestyleObservation(
            task_type=self._task["task_type"],
            user_profile=self._task["user_profile"],
            context=self._task["context"],
            step_index=step_index,
            instruction=instruction,
            feedback=self._last_feedback if step_index > 0 else None,
        )
=======
from lifestyle_planner_env.models import (
    LifestyleAction,
    LifestyleObservation,
    LifestyleState,
    LifestyleTask,
    StepResult
)


class LifestylePlannerEnv:
    def __init__(self):
        self.reset()

    def reset(self):
        self.current_time = 0
        self.max_time = 8
        self.energy_level = 10
        self.total_reward = 0.0

        self.tasks = [
            LifestyleTask(name="Study", priority=5, duration=3, deadline=4),
            LifestyleTask(name="Workout", priority=4, duration=2, deadline=6),
            LifestyleTask(name="Assignment", priority=6, duration=2, deadline=3),
        ]

        self.completed_tasks = []

        return self.state()

    def state(self):
        return LifestyleState(
            current_time=self.current_time,
            max_time=self.max_time,
            energy_level=self.energy_level,
            tasks=self.tasks,
            completed_tasks=self.completed_tasks,
            total_reward=self.total_reward
        )

    def step(self, action: LifestyleAction):
        self.current_time += 1
        reward = 0.0

        chosen_task = next(
            (task for task in self.tasks if task.name == action.task_name),
            None
        )

        if chosen_task:
            chosen_task.duration -= 1
            self.energy_level -= 1
            reward += chosen_task.priority * 0.5

            if chosen_task.duration <= 0:
                self.completed_tasks.append(chosen_task.name)
                self.tasks.remove(chosen_task)
                reward += chosen_task.priority * 2
        else:
            reward -= 2.0  # invalid or wasted action

        # deadline penalties
        for task in self.tasks:
            if self.current_time > task.deadline:
                reward -= task.priority * 1.0

        # burnout penalty
        if self.energy_level <= 2:
            reward -= 3.0

        self.total_reward += reward
        done = self.current_time >= self.max_time or len(self.tasks) == 0

        observation = LifestyleObservation(
            current_time=self.current_time,
            max_time=self.max_time,
            energy_level=self.energy_level,
            tasks=self.tasks,
            completed_tasks=self.completed_tasks
        )

        return StepResult(
            observation=observation,
            reward=reward,
            done=done,
            info={"total_reward": self.total_reward}
        )
    
>>>>>>> 6d39c54215ae40124371e71bc5c5390de8d5fe7e
