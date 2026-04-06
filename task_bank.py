<<<<<<< HEAD
"""
task_bank.py — Parameterized task generator for the Lifestyle Planner Environment.

Design principles:
- Tasks are generated (not hardcoded) so each episode is distinct.
- Three difficulty levels per task type control how constrained the scenario is.
- Each task carries a grading rubric that the grader uses directly,
  keeping task specification and grading criteria co-located.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Literal, TypedDict

DifficultyLevel = Literal["easy", "medium", "hard"]


# ---------------------------------------------------------------------------
# Typed task structure
# ---------------------------------------------------------------------------

class Task(TypedDict):
    task_type: str
    difficulty: DifficultyLevel
    user_profile: Dict[str, Any]   # stable user facts
    context: Dict[str, Any]        # task-specific dynamic context
    instruction: str               # natural language prompt for the agent
    rubric: Dict[str, float]       # criterion_name → max_points (must sum to 1.0)


# ---------------------------------------------------------------------------
# Task generators
# ---------------------------------------------------------------------------

def _sample_plan_day(difficulty: DifficultyLevel) -> Task:
    """
    plan_day: agent must produce a realistic daily schedule given energy
    level, fixed commitments, and personal goals.
    """

    configs = {
        "easy": {
            "sleep_hours": 8,
            "energy_level": 8,        # 1-10 scale
            "fixed_events": ["team standup 10:00-10:30"],
            "goals": ["deep work", "exercise"],
            "free_blocks": ["07:00-10:00", "11:00-18:00"],
            "deadline_pressure": "none",
        },
        "medium": {
            "sleep_hours": 6,
            "energy_level": 5,
            "fixed_events": ["college 10:00-14:00", "family dinner 19:00-20:00"],
            "goals": ["study", "workout", "side project"],
            "free_blocks": ["07:00-10:00", "14:30-19:00", "20:00-22:00"],
            "deadline_pressure": "exam in 2 days",
        },
        "hard": {
            "sleep_hours": 4,
            "energy_level": 3,
            "fixed_events": [
                "client call 09:00-10:00",
                "lecture 11:00-13:00",
                "group project 15:00-17:00",
            ],
            "goals": ["study", "workout", "job applications", "self-care"],
            "free_blocks": ["07:00-09:00", "13:00-15:00", "17:30-22:00"],
            "deadline_pressure": "interview tomorrow, exam in 3 days",
        },
    }

    cfg = configs[difficulty]
    return Task(
        task_type="plan_day",
        difficulty=difficulty,
        user_profile={
            "sleep_hours_last_night": cfg["sleep_hours"],
            "energy_level": cfg["energy_level"],
            "goals": cfg["goals"],
        },
        context={
            "fixed_events": cfg["fixed_events"],
            "free_time_blocks": cfg["free_blocks"],
            "deadline_pressure": cfg["deadline_pressure"],
        },
        instruction=(
            "Create a realistic, prioritized daily schedule. "
            "Account for the user's energy level, honor all fixed events, "
            "address their goals, and include recovery time. "
            "Output a structured plan with explicit time blocks."
        ),
        rubric={
            "goal_coverage":        0.25,  # all stated goals addressed
            "energy_awareness":     0.20,  # hard tasks matched to high-energy windows
            "schedule_feasibility": 0.20,  # blocks don't overlap; total ≤ free time
            "recovery_inclusion":   0.20,  # meals, breaks, wind-down present
            "deadline_handling":    0.15,  # deadline acknowledged with concrete action
        },
    )


def _sample_recover_day(difficulty: DifficultyLevel) -> Task:
    """
    recover_day: agent must salvage a partially-failed day, triage tasks,
    and help the user end the day on a productive, healthy note.
    """

    configs = {
        "easy": {
            "woke_up_late_by_min": 30,
            "missed_tasks": ["morning workout"],
            "screen_time_hours": 1.5,
            "energy_level": 6,
            "remaining_window": "14:00-22:00",
            "must_complete": ["finish one chapter"],
        },
        "medium": {
            "woke_up_late_by_min": 90,
            "missed_tasks": ["workout", "morning study block"],
            "screen_time_hours": 3,
            "energy_level": 3,
            "remaining_window": "15:00-22:00",
            "must_complete": ["study 2 hrs", "reply to emails"],
        },
        "hard": {
            "woke_up_late_by_min": 180,
            "missed_tasks": ["workout", "morning study", "meal prep"],
            "screen_time_hours": 5,
            "energy_level": 2,
            "remaining_window": "17:00-23:00",
            "must_complete": ["study 3 hrs", "submit assignment", "gym or walk"],
        },
    }

    cfg = configs[difficulty]
    return Task(
        task_type="recover_day",
        difficulty=difficulty,
        user_profile={
            "energy_level": cfg["energy_level"],
            "screen_time_hours_so_far": cfg["screen_time_hours"],
        },
        context={
            "woke_up_late_by_minutes": cfg["woke_up_late_by_min"],
            "missed_tasks": cfg["missed_tasks"],
            "remaining_time_window": cfg["remaining_window"],
            "must_complete_today": cfg["must_complete"],
        },
        instruction=(
            "The user's day has gone off-track. Diagnose what went wrong, "
            "triage remaining tasks by urgency and energy cost, "
            "and produce a recovery schedule for the remaining hours. "
            "Be realistic — do not pretend the full original plan is recoverable."
        ),
        rubric={
            "triage_quality":         0.25,  # correct prioritization of must-do tasks
            "realism":                0.25,  # plan fits within the remaining window
            "damage_control":         0.20,  # addresses missed tasks where possible
            "wellbeing_preservation": 0.20,  # prevents further spiral (sleep, food)
            "screen_time_strategy":   0.10,  # actively addresses excess screen time
        },
    )


def _sample_optimize_week(difficulty: DifficultyLevel) -> Task:
    """
    optimize_week: agent must produce a 7-day routine template that
    systematically achieves weekly goals while correcting past failure patterns.
    """

    configs = {
        "easy": {
            "weekly_goals": ["study 10 hrs", "gym 3x", "sleep 7+ hrs nightly"],
            "past_failures": ["inconsistent sleep"],
            "constraints": ["college Mon-Fri 10:00-14:00"],
            "available_days_off": ["Sunday"],
        },
        "medium": {
            "weekly_goals": ["study 15 hrs", "gym 4x", "sleep 7+ hrs", "read 1 hr/day"],
            "past_failures": ["late sleep", "skipped gym on Wed/Fri", "irregular meals"],
            "constraints": ["college Mon-Fri 10:00-14:00", "part-time job Sat 10:00-15:00"],
            "available_days_off": [],
        },
        "hard": {
            "weekly_goals": [
                "study 20 hrs", "gym 5x", "sleep 7+ hrs",
                "side project 5 hrs", "social commitments Sat evening",
            ],
            "past_failures": [
                "burnout by Wednesday", "skipped gym when tired",
                "binge screens after 22:00", "skipped meals",
            ],
            "constraints": [
                "college Mon-Fri 09:00-15:00",
                "part-time job Tue/Thu 16:00-19:00",
                "family obligation Sunday morning",
            ],
            "available_days_off": [],
        },
    }

    cfg = configs[difficulty]
    return Task(
        task_type="optimize_week",
        difficulty=difficulty,
        user_profile={
            "weekly_goals": cfg["weekly_goals"],
            "documented_failure_patterns": cfg["past_failures"],
        },
        context={
            "fixed_constraints": cfg["constraints"],
            "available_rest_days": cfg["available_days_off"],
        },
        instruction=(
            "Design a 7-day routine template that reliably achieves the user's "
            "weekly goals. Explicitly address each documented failure pattern with "
            "a concrete countermeasure. Include fallback rules for when plans slip. "
            "Output a day-by-day structure with time blocks."
        ),
        rubric={
            "goal_achievement_coverage": 0.30,  # each weekly goal has allocated time
            "failure_pattern_addressing": 0.25,  # each past failure has a countermeasure
            "schedule_sustainability":    0.20,  # no day is overwhelmingly packed
            "fallback_rules_present":     0.15,  # explicit if-then rules for slip days
            "constraint_compliance":      0.10,  # fixed constraints respected throughout
        },
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_GENERATORS = {
    "plan_day":      _sample_plan_day,
    "recover_day":   _sample_recover_day,
    "optimize_week": _sample_optimize_week,
}

TASK_TYPES = list(_GENERATORS.keys())
DIFFICULTY_LEVELS: list[DifficultyLevel] = ["easy", "medium", "hard"]


def sample_task(
    task_type: str | None = None,
    difficulty: DifficultyLevel | None = None,
) -> Task:
    """
    Return a Task dict, optionally pinning task_type and/or difficulty.
    If either is None, it is chosen uniformly at random.
    """
    if task_type is None:
        task_type = random.choice(TASK_TYPES)
    if difficulty is None:
        difficulty = random.choice(DIFFICULTY_LEVELS)

    if task_type not in _GENERATORS:
        raise ValueError(f"Unknown task_type '{task_type}'. Valid: {TASK_TYPES}")

    return _GENERATORS[task_type](difficulty)
=======
TASKS = [
    {
        "task_type": "plan_day",
        "input": {
            "sleep_hours": 6,
            "energy": 5,
            "fixed_events": ["college 10-2"],
            "goals": ["study", "workout"],
            "free_time_blocks": ["7-9 AM", "5-8 PM"],
            "deadline": "exam in 2 days"
        }
    },
    {
        "task_type": "recover_day",
        "input": {
            "woke_up_late": True,
            "missed_tasks": ["workout"],
            "screen_time_hours": 3,
            "energy": 3,
            "remaining_time": "5-10 PM",
            "goals": ["study", "health"]
        }
    },
    {
        "task_type": "optimize_week",
        "input": {
            "weekly_goal": ["study 15 hrs", "gym 4x", "sleep 7+ hrs"],
            "past_failures": ["late sleep", "skipped gym"],
            "constraints": ["college", "assignments"]
        }
    }
]
>>>>>>> 6d39c54215ae40124371e71bc5c5390de8d5fe7e
