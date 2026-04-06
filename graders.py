<<<<<<< HEAD
"""
graders.py — Rubric-based graders for the Lifestyle Planner Environment.

Design principles:
- Each grader maps to a task type and evaluates structured LifestyleAction objects,
  not raw strings. This enables per-criterion scoring.
- Grading uses heuristics that are transparent and justifiable:
    * structural checks (does the schedule cover required time windows?)
    * coverage checks (are all stated goals represented in time blocks?)
    * plausibility checks (do block durations add up? are strategies named?)
  These are imperfect but far more defensible than bare keyword matching.
- Each grader returns a dict[criterion → score] so the environment can
  surface per-criterion feedback to the agent on intermediate steps.
- The rubric lives on the Task object; graders reference it for weights.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

from models import LifestyleAction, TimeBlock


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def _parse_time(t: str) -> datetime | None:
    """Parse 'HH:MM' strings, return None if unparseable."""
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(t.strip(), fmt)
        except ValueError:
            pass
    return None


def _block_minutes(block: TimeBlock) -> float:
    """Return duration of a TimeBlock in minutes, or 0 if unparseable."""
    start = _parse_time(block.start)
    end   = _parse_time(block.end)
    if start is None or end is None:
        return 0.0
    delta = (end - start).total_seconds() / 60
    return max(delta, 0.0)


def _schedule_is_feasible(schedule: List[TimeBlock]) -> Tuple[bool, str]:
    """
    Check that time blocks are ordered and non-overlapping.
    Returns (ok, explanation).
    """
    times = []
    for blk in schedule:
        s = _parse_time(blk.start)
        e = _parse_time(blk.end)
        if s is None or e is None:
            return False, f"Unparseable time in block '{blk.activity}'"
        if e <= s:
            return False, f"Block '{blk.activity}' ends before it starts"
        times.append((s, e, blk.activity))

    times.sort(key=lambda x: x[0])
    for i in range(len(times) - 1):
        if times[i][1] > times[i + 1][0]:
            return False, (
                f"Overlap: '{times[i][2]}' and '{times[i+1][2]}'"
            )
    return True, "ok"


def _goals_covered(goals: List[str], schedule: List[TimeBlock]) -> float:
    """
    Fraction of goals that appear (keyword-matched) in at least one
    scheduled activity. Uses normalized matching (gym ≈ workout ≈ exercise).
    """
    synonym_groups = [
        {"gym", "workout", "exercise", "training", "run", "jog", "walk"},
        {"study", "studying", "revision", "review", "learn", "reading"},
        {"sleep", "rest", "nap", "wind-down", "bedtime"},
        {"meal", "eat", "breakfast", "lunch", "dinner", "food"},
        {"work", "deep work", "focus", "project", "code", "write"},
    ]

    def normalize(text: str) -> set[str]:
        words = set(re.findall(r"\w+", text.lower()))
        for group in synonym_groups:
            if words & group:
                words |= group
        return words

    all_activity_words: set[str] = set()
    for blk in schedule:
        all_activity_words |= normalize(blk.activity)
        if blk.rationale:
            all_activity_words |= normalize(blk.rationale)

    covered = 0
    for goal in goals:
        goal_words = normalize(goal)
        if goal_words & all_activity_words:
            covered += 1

    return covered / max(len(goals), 1)


def _has_recovery_blocks(schedule: List[TimeBlock]) -> float:
    """
    Score 0–1 for presence of wellbeing blocks (meals, breaks, wind-down).
    Partial credit per category found.
    """
    categories = {
        "meal":    {"meal", "breakfast", "lunch", "dinner", "eat", "food"},
        "break":   {"break", "rest", "stretch", "walk", "refresh"},
        "sleep":   {"sleep", "wind-down", "bedtime", "nap"},
    }
    found = 0
    for blk in schedule:
        words = set(re.findall(r"\w+", blk.activity.lower()))
        for cat_words in categories.values():
            if words & cat_words:
                found += 1
                break

    return min(found / len(categories), 1.0)


def _strategies_quality(strategies: List[str]) -> float:
    """
    Score strategy list quality.
    - ≥3 named strategies → full credit
    - Generic/empty → partial credit
    Real strategies: time-blocking, energy-matching, habit stacking, etc.
    Penalise single-word or very short entries.
    """
    substantive = [s for s in strategies if len(s.split()) >= 2]
    return min(len(substantive) / 3, 1.0)


def _calibration_score(self_score: float, actual_score: float) -> float:
    """
    Reward agents that accurately estimate their own plan quality.
    Full credit if |self - actual| < 0.1, linearly decays to 0 at delta=0.5.
    """
    delta = abs(self_score - actual_score)
    return max(0.0, 1.0 - delta * 2)


# ---------------------------------------------------------------------------
# Per-task graders
# ---------------------------------------------------------------------------

def grade_plan_day(
    action: LifestyleAction,
    task_input: Dict[str, Any],
    rubric: Dict[str, float],
) -> Dict[str, float]:
    """
    Rubric:
        goal_coverage        — stated goals appear in schedule
        energy_awareness     — hard activities in first half of free blocks
        schedule_feasibility — no overlaps, parseable times
        recovery_inclusion   — meals/breaks/sleep present
        deadline_handling    — deadline mentioned and addressed in summary/notes
    """
    scores: Dict[str, float] = {}

    goals = task_input.get("user_profile", {}).get("goals", [])
    scores["goal_coverage"] = _goals_covered(goals, action.schedule)

    feasible, _ = _schedule_is_feasible(action.schedule)
    scores["schedule_feasibility"] = 1.0 if feasible else 0.3

    scores["recovery_inclusion"] = _has_recovery_blocks(action.schedule)

    # Energy awareness: high-priority blocks should appear early
    high_priority = [b for b in action.schedule if b.priority == "high"]
    if high_priority:
        # Reward if high-priority blocks start before 15:00
        early = sum(1 for b in high_priority if _parse_time(b.start) and
                    _parse_time(b.start).hour < 15)
        scores["energy_awareness"] = early / len(high_priority)
    else:
        scores["energy_awareness"] = 0.4  # partial: at least they have a plan

    deadline = task_input.get("context", {}).get("deadline_pressure", "none")
    text = (action.summary + " " + (action.notes or "")).lower()
    if deadline != "none" and any(w in text for w in ["exam", "interview", "deadline", "urgent"]):
        scores["deadline_handling"] = 1.0
    elif deadline == "none":
        scores["deadline_handling"] = 1.0  # no deadline to handle → full credit
    else:
        scores["deadline_handling"] = 0.0

    return {k: round(v, 3) for k, v in scores.items()}


def grade_recover_day(
    action: LifestyleAction,
    task_input: Dict[str, Any],
    rubric: Dict[str, float],
) -> Dict[str, float]:
    """
    Rubric:
        triage_quality         — must-complete tasks appear in schedule
        realism                — schedule fits within remaining window
        damage_control         — missed tasks partially addressed
        wellbeing_preservation — sleep/meals present
        screen_time_strategy   — explicit screen time limits mentioned
    """
    scores: Dict[str, float] = {}

    must_complete = task_input.get("context", {}).get("must_complete_today", [])
    scores["triage_quality"] = _goals_covered(must_complete, action.schedule)

    # Realism: total scheduled minutes ≤ available window
    window_str = task_input.get("context", {}).get("remaining_time_window", "")
    parts = re.findall(r"\d{2}:\d{2}", window_str)
    if len(parts) == 2:
        w_start = _parse_time(parts[0])
        w_end   = _parse_time(parts[1])
        if w_start and w_end:
            available_min = (w_end - w_start).total_seconds() / 60
            scheduled_min = sum(_block_minutes(b) for b in action.schedule)
            overrun_ratio = max(scheduled_min / max(available_min, 1) - 1.0, 0)
            scores["realism"] = max(0.0, 1.0 - overrun_ratio * 2)
        else:
            scores["realism"] = 0.5
    else:
        scores["realism"] = 0.5

    missed = task_input.get("context", {}).get("missed_tasks", [])
    scores["damage_control"] = _goals_covered(missed, action.schedule) * 0.7 + 0.3
    # Note: partial credit even if missed tasks can't be recovered (realistic)

    scores["wellbeing_preservation"] = _has_recovery_blocks(action.schedule)

    text = (action.summary + " " + (action.notes or "")).lower()
    screen_words = {"screen", "phone", "social media", "limit", "digital", "doom"}
    scores["screen_time_strategy"] = (
        1.0 if any(w in text for w in screen_words) else 0.0
    )

    return {k: round(v, 3) for k, v in scores.items()}


def grade_optimize_week(
    action: LifestyleAction,
    task_input: Dict[str, Any],
    rubric: Dict[str, float],
) -> Dict[str, float]:
    """
    Rubric:
        goal_achievement_coverage  — each weekly goal has dedicated schedule blocks
        failure_pattern_addressing — each past failure has a named countermeasure
        schedule_sustainability    — no day > 10 hrs of structured activity
        fallback_rules_present     — if-then language present in notes/summary
        constraint_compliance      — fixed constraints not scheduled over
    """
    scores: Dict[str, float] = {}

    weekly_goals = task_input.get("user_profile", {}).get("weekly_goals", [])
    scores["goal_achievement_coverage"] = _goals_covered(weekly_goals, action.schedule)

    failures = task_input.get("user_profile", {}).get("documented_failure_patterns", [])
    full_text = (action.summary + " " + " ".join(action.strategies) + " " + (action.notes or "")).lower()
    addressed = sum(
        1 for f in failures
        if any(word in full_text for word in re.findall(r"\w+", f.lower()))
    )
    scores["failure_pattern_addressing"] = addressed / max(len(failures), 1)

    # Sustainability: average block count per "day" should be manageable
    # (heuristic: if schedule has many blocks, check total minutes)
    total_hours = sum(_block_minutes(b) for b in action.schedule) / 60
    blocks_per_day = total_hours / 7  # approximate
    scores["schedule_sustainability"] = max(0.0, 1.0 - max(blocks_per_day - 10, 0) / 4)

    fallback_markers = {"if", "fallback", "when", "miss", "slip", "backup", "alternative"}
    scores["fallback_rules_present"] = (
        1.0 if any(m in full_text for m in fallback_markers) else 0.0
    )

    constraints = task_input.get("context", {}).get("fixed_constraints", [])
    # Simple check: constraint keywords don't appear as "free" activities
    # (Heuristic: if agent explicitly calls a constraint block "free study", flag it)
    violations = 0
    for constraint in constraints:
        c_words = set(re.findall(r"\w+", constraint.lower()))
        for blk in action.schedule:
            act_words = set(re.findall(r"\w+", blk.activity.lower()))
            if c_words & act_words and blk.priority == "low":
                violations += 1
    scores["constraint_compliance"] = max(0.0, 1.0 - violations * 0.25)

    return {k: round(v, 3) for k, v in scores.items()}


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate_score(
    criterion_scores: Dict[str, float],
    rubric: Dict[str, float],
) -> float:
    """
    Compute weighted sum of criterion scores using the task's rubric weights.
    Returns a float in [0, 1].
    """
    total = 0.0
    for criterion, weight in rubric.items():
        total += criterion_scores.get(criterion, 0.0) * weight
    return round(min(total, 1.0), 4)


def generate_feedback(
    criterion_scores: Dict[str, float],
    rubric: Dict[str, float],
    task_type: str,
) -> str:
    """
    Produce a natural-language feedback string from criterion scores.
    Used to populate the next observation's `feedback` field.
    """
    lines = [f"Step feedback for task '{task_type}':"]
    for criterion, weight in rubric.items():
        score = criterion_scores.get(criterion, 0.0)
        bar = "█" * int(score * 5) + "░" * (5 - int(score * 5))
        lines.append(f"  {bar} {criterion}: {score:.2f} (weight {weight:.0%})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public dispatch
# ---------------------------------------------------------------------------

_GRADERS = {
    "plan_day":      grade_plan_day,
    "recover_day":   grade_recover_day,
    "optimize_week": grade_optimize_week,
}


def grade_action(
    task_type: str,
    action: LifestyleAction,
    task_input: Dict[str, Any],
    rubric: Dict[str, float],
) -> Tuple[Dict[str, float], float, str]:
    """
    Grade an action against a task.

    Returns:
        criterion_scores : per-criterion float scores
        total_score      : weighted aggregate in [0, 1]
        feedback         : natural-language feedback string
    """
    if task_type not in _GRADERS:
        raise ValueError(f"No grader for task_type '{task_type}'")

    criterion_scores = _GRADERS[task_type](action, task_input, rubric)
    total_score = aggregate_score(criterion_scores, rubric)
    feedback = generate_feedback(criterion_scores, rubric, task_type)

    return criterion_scores, total_score, feedback
=======
def grade_plan_day(plan: str, task_input: dict) -> float:
    score = 0.0
    text = plan.lower()

    if "study" in text:
        score += 0.25
    if "workout" in text or "exercise" in text:
        score += 0.25
    if "sleep" in text:
        score += 0.25
    if any(word in text for word in ["break", "rest", "meal"]):
        score += 0.25

    return min(score, 1.0)


def grade_recover_day(plan: str, task_input: dict) -> float:
    score = 0.0
    text = plan.lower()

    if any(word in text for word in ["prioritize", "focus", "important"]):
        score += 0.25
    if any(word in text for word in ["sleep", "rest"]):
        score += 0.25
    if any(word in text for word in ["walk", "exercise", "movement", "workout"]):
        score += 0.25
    if any(word in text for word in ["screen", "phone", "limit"]):
        score += 0.25

    return min(score, 1.0)


def grade_optimize_week(plan: str, task_input: dict) -> float:
    score = 0.0
    text = plan.lower()

    if "study" in text:
        score += 0.25
    if any(word in text for word in ["gym", "workout", "exercise"]):
        score += 0.25
    if "sleep" in text:
        score += 0.25
    if any(word in text for word in ["consistency", "routine", "fallback", "habit"]):
        score += 0.25

    return min(score, 1.0)


def grade_task(task_type: str, plan: str, task_input: dict) -> float:
    if task_type == "plan_day":
        return grade_plan_day(plan, task_input)
    elif task_type == "recover_day":
        return grade_recover_day(plan, task_input)
    elif task_type == "optimize_week":
        return grade_optimize_week(plan, task_input)
    return 0.0
>>>>>>> 6d39c54215ae40124371e71bc5c5390de8d5fe7e
