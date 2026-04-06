<<<<<<< HEAD
"""
baseline_inference.py — Real LLM baseline agent + evaluation harness.

This module serves two purposes:
1. Define a baseline agent that calls a real LLM (via the Anthropic SDK)
   to generate structured LifestyleAction responses.
2. Run a benchmark across all task types and difficulty levels, collecting
   aggregate statistics that can be reported in the README and demo.

Usage:
    python baseline_inference.py                  # full benchmark
    python baseline_inference.py --single         # single episode demo
    python baseline_inference.py --task plan_day  # single task type, all difficulties

Requirements:
    pip install anthropic
    export ANTHROPIC_API_KEY=...
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from statistics import mean, stdev
from typing import Any, Dict, List

try:
    import anthropic
except ImportError:
    print("Run: pip install anthropic")
    sys.exit(1)

from models import LifestyleAction, TimeBlock
from server.lifestyle_planner_environment import LifestylePlannerEnvironment
from task_bank import DIFFICULTY_LEVELS, TASK_TYPES


# ---------------------------------------------------------------------------
# LLM agent
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = textwrap.dedent("""
You are an expert lifestyle and productivity coach. When given a lifestyle
planning task, you output a structured JSON object — and ONLY that object,
with no preamble or explanation.

The JSON must match this exact schema:
{
  "summary": "<one paragraph executive summary of the plan, max 400 chars>",
  "schedule": [
    {
      "start": "<HH:MM>",
      "end": "<HH:MM>",
      "activity": "<what the user does>",
      "priority": "<high|medium|low>",
      "rationale": "<why this block is scheduled here>"
    }
  ],
  "strategies": ["<named strategy 1>", "<named strategy 2>", ...],
  "self_score": <float 0.0-1.0, your honest estimate of plan quality>,
  "notes": "<optional caveats, assumptions, or edge-case handling>"
}

Rules:
- Include at least 4 time blocks in the schedule.
- Times must be in HH:MM 24-hour format.
- Strategies must be named (e.g. 'energy-matching', 'time-blocking').
- self_score must reflect your genuine confidence in the plan quality.
- Output raw JSON only — no markdown, no ```json fences.
""").strip()


def build_user_prompt(obs) -> str:
    """Convert an observation into a user-turn prompt for the LLM."""
    parts = [
        f"Task: {obs.task_type}",
        f"Step: {obs.step_index}",
        f"\nInstruction:\n{obs.instruction}",
        f"\nUser Profile:\n{json.dumps(obs.user_profile, indent=2)}",
        f"\nContext:\n{json.dumps(obs.context, indent=2)}",
    ]
    if obs.feedback:
        parts.append(f"\nPrevious Step Feedback:\n{obs.feedback}")
    return "\n".join(parts)


def parse_llm_response(raw: str) -> LifestyleAction:
    """
    Parse the LLM's JSON response into a LifestyleAction.
    Falls back gracefully if the model produces malformed output.
    """
    try:
        data = json.loads(raw.strip())
        schedule = [TimeBlock(**blk) for blk in data.get("schedule", [])]
        return LifestyleAction(
            summary=data.get("summary", "No summary provided."),
            schedule=schedule,
            strategies=data.get("strategies", ["general planning"]),
            self_score=float(data.get("self_score", 0.5)),
            notes=data.get("notes"),
        )
    except Exception as exc:
        # Fallback: return a minimal valid action so grading can still proceed
        print(f"  [warn] Failed to parse LLM response: {exc}")
        return LifestyleAction(
            summary=raw[:400],
            schedule=[
                TimeBlock(start="08:00", end="09:00", activity="Study", priority="high"),
                TimeBlock(start="09:00", end="09:30", activity="Break", priority="low"),
            ],
            strategies=["fallback plan"],
            self_score=0.3,
            notes="Parse error — fallback action used.",
        )


class LLMAgent:
    """Calls Claude to generate LifestyleAction responses."""

    def __init__(self, model: str = "claude-opus-4-5"):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY not set.")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def act(self, obs) -> LifestyleAction:
        prompt = build_user_prompt(obs)
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        return parse_llm_response(raw)


# ---------------------------------------------------------------------------
# Deterministic baseline (no LLM dependency, for CI/offline use)
# ---------------------------------------------------------------------------

class RuleBasedAgent:
    """
    Deterministic rule-based agent for offline benchmarking.
    Produces structured (not just string) responses, so it's a fair comparison.
    """

    _PLANS: Dict[str, Dict[str, Any]] = {
        "plan_day": {
            "summary": (
                "Prioritize high-energy tasks in the morning using time-blocking. "
                "Schedule study and work in focused 90-minute blocks. "
                "Include meals, short breaks, and wind-down before sleep."
            ),
            "schedule": [
                {"start": "07:00", "end": "07:30", "activity": "Breakfast and planning", "priority": "high", "rationale": "fuel before cognitive work"},
                {"start": "07:30", "end": "09:00", "activity": "Study — deep work session", "priority": "high", "rationale": "peak energy window"},
                {"start": "09:00", "end": "09:15", "activity": "Break — walk or stretch", "priority": "low", "rationale": "recovery between blocks"},
                {"start": "14:30", "end": "16:00", "activity": "Study — review and practice", "priority": "high", "rationale": "post-class consolidation"},
                {"start": "17:00", "end": "18:00", "activity": "Workout / exercise", "priority": "medium", "rationale": "energy-matching with lower cognitive load"},
                {"start": "19:00", "end": "19:30", "activity": "Dinner", "priority": "medium", "rationale": "recovery meal"},
                {"start": "21:30", "end": "22:00", "activity": "Wind-down — no screens", "priority": "medium", "rationale": "sleep quality"},
            ],
            "strategies": ["time-blocking", "energy-matching", "habit stacking", "Pomodoro technique"],
            "self_score": 0.72,
            "notes": "Assumes fixed events are respected. Exam deadline addressed via morning study blocks.",
        },
        "recover_day": {
            "summary": (
                "Triage remaining tasks: complete must-dos in the remaining window. "
                "Accept missed tasks, limit screen time, and protect sleep. "
                "One short exercise block to restore energy."
            ),
            "schedule": [
                {"start": "15:30", "end": "15:45", "activity": "Meal / snack", "priority": "high", "rationale": "fuel before evening work"},
                {"start": "15:45", "end": "17:15", "activity": "Study — priority tasks only", "priority": "high", "rationale": "must-complete task first"},
                {"start": "17:15", "end": "17:45", "activity": "Walk or light exercise", "priority": "medium", "rationale": "damage control for missed workout"},
                {"start": "18:00", "end": "18:30", "activity": "Dinner", "priority": "medium", "rationale": "regular meal time"},
                {"start": "18:30", "end": "20:00", "activity": "Study — second block", "priority": "high", "rationale": "complete daily quota"},
                {"start": "20:00", "end": "20:30", "activity": "Break — limit phone to 15 min", "priority": "medium", "rationale": "screen time reduction strategy"},
                {"start": "21:30", "end": "22:00", "activity": "Wind-down — sleep by 22:30", "priority": "high", "rationale": "prevent further spiral"},
            ],
            "strategies": ["triage and prioritize", "damage-control mindset", "screen time budgeting", "sleep anchoring"],
            "self_score": 0.68,
            "notes": "If energy is 2/10, replace second study block with a rest period. Fallback: sleep by 22:00.",
        },
        "optimize_week": {
            "summary": (
                "Build a sustainable 7-day template with dedicated blocks for each goal. "
                "Address past failure patterns with explicit countermeasures. "
                "Include fallback rules for slip days."
            ),
            "schedule": [
                {"start": "07:00", "end": "09:00", "activity": "Study block — Mon/Tue/Thu", "priority": "high", "rationale": "consistent morning habit"},
                {"start": "17:00", "end": "18:30", "activity": "Gym workout — Mon/Wed/Fri/Sat", "priority": "high", "rationale": "gym 4x weekly goal"},
                {"start": "22:00", "end": "07:00", "activity": "Sleep — hard cutoff at 22:30", "priority": "high", "rationale": "7+ hrs sleep goal; countermeasure for late sleep failure"},
                {"start": "12:00", "end": "13:00", "activity": "Lunch and rest", "priority": "medium", "rationale": "recovery mid-day"},
                {"start": "19:00", "end": "21:00", "activity": "Study block — Wed/Fri/Sun", "priority": "high", "rationale": "15 hr weekly study total"},
                {"start": "21:00", "end": "21:30", "activity": "Wind-down routine", "priority": "medium", "rationale": "fallback trigger for sleep cutoff"},
                {"start": "08:00", "end": "10:00", "activity": "Flexible / rest — Sunday", "priority": "low", "rationale": "active recovery day"},
            ],
            "strategies": ["habit stacking", "consistency over intensity", "fallback rule design", "load balancing"],
            "self_score": 0.75,
            "notes": (
                "Fallback rules: if gym missed, substitute a 30-min walk. "
                "If late sleep pattern returns, move wind-down 30 min earlier. "
                "Study hours tracked weekly — miss a day, make it up on Sunday."
            ),
        },
    }

    def act(self, obs) -> LifestyleAction:
        plan = self._PLANS[obs.task_type]
        schedule = [TimeBlock(**blk) for blk in plan["schedule"]]
        return LifestyleAction(
            summary=plan["summary"],
            schedule=schedule,
            strategies=plan["strategies"],
            self_score=plan["self_score"],
            notes=plan.get("notes"),
        )


# ---------------------------------------------------------------------------
# Evaluation harness
# ---------------------------------------------------------------------------

def run_episode(
    env: LifestylePlannerEnvironment,
    agent,
    task_type: str | None = None,
    difficulty: str | None = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run one full episode and return result dict."""
    obs = env.reset(task_type=task_type, difficulty=difficulty)

    if verbose:
        print(f"\n{'='*60}")
        print(f"Task: {obs.task_type}  |  Difficulty: {env.state().difficulty}")
        print(f"Instruction: {obs.instruction[:120]}...")

    step_scores = []
    done = False
    info = {}

    while not done:
        action = agent.act(obs)
        obs, reward, done, info = env.step(action)
        step_scores.append(reward)

        if verbose:
            print(f"\n--- Step {len(step_scores)} score: {reward:.3f} ---")
            if obs.feedback:
                print(obs.feedback)

    final_state = env.state()
    result = {
        "episode_id":       final_state.episode_id,
        "task_type":        final_state.task_type,
        "difficulty":       final_state.difficulty,
        "step_scores":      step_scores,
        "cumulative_score": final_state.cumulative_score,
    }

    if verbose:
        print(f"\n✓ Episode complete. Cumulative score: {final_state.cumulative_score:.3f}")

    return result


def run_benchmark(agent, n_episodes_per_combo: int = 3) -> None:
    """
    Run N episodes for every (task_type × difficulty) combination.
    Print a summary table.
    """
    env = LifestylePlannerEnvironment()
    results: List[Dict[str, Any]] = []

    combos = [
        (tt, diff)
        for tt in TASK_TYPES
        for diff in DIFFICULTY_LEVELS
    ]

    print(f"\nRunning benchmark: {len(combos)} combinations × {n_episodes_per_combo} episodes")
    print("=" * 64)

    for task_type, difficulty in combos:
        combo_scores = []
        for _ in range(n_episodes_per_combo):
            result = run_episode(env, agent, task_type=task_type, difficulty=difficulty)
            results.append(result)
            combo_scores.append(result["cumulative_score"])

        avg = mean(combo_scores)
        sd  = stdev(combo_scores) if len(combo_scores) > 1 else 0.0
        print(f"  {task_type:<18} {difficulty:<8}  avg={avg:.3f}  std={sd:.3f}")

    all_scores = [r["cumulative_score"] for r in results]
    print("=" * 64)
    print(f"  Overall: avg={mean(all_scores):.3f}  std={stdev(all_scores):.3f}  n={len(all_scores)}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Lifestyle Planner Env baseline")
    parser.add_argument("--single",   action="store_true", help="Run one episode demo")
    parser.add_argument("--task",     default=None,        help="Pin task type")
    parser.add_argument("--llm",      action="store_true", help="Use LLM agent (requires API key)")
    parser.add_argument("--episodes", type=int, default=3, help="Episodes per combo in benchmark")
    args = parser.parse_args()

    agent = LLMAgent() if args.llm else RuleBasedAgent()
    agent_name = "LLM (Claude)" if args.llm else "Rule-based"
    print(f"Agent: {agent_name}")

    env = LifestylePlannerEnvironment()

    if args.single or args.task:
        run_episode(env, agent, task_type=args.task, verbose=True)
    else:
        run_benchmark(agent, n_episodes_per_combo=args.episodes)


if __name__ == "__main__":
    main()
=======
from lifestyle_planner_env.server.lifestyle_planner_environment import LifestylePlannerEnv
from lifestyle_planner_env.models import LifestyleAction
from lifestyle_planner_env.graders import grade_episode


def choose_action(observation):
    """
    Simple heuristic baseline:
    choose task by urgency-adjusted priority
    """

    if not observation.tasks:
        return None

    def task_score(task):
        urgency = max(1, task.deadline - observation.current_time)
        return (task.priority / max(1, task.duration)) + (1 / urgency)

    best_task = max(observation.tasks, key=task_score)
    return LifestyleAction(task_name=best_task.name)


def run_baseline_for_difficulty(difficulty: str):
    env = LifestylePlannerEnv(difficulty=difficulty)
    obs = env.reset()

    done = False

    while not done:
        action = choose_action(obs)
        if action is None:
            break

        result = env.step(action)
        obs = result.observation
        done = result.done

    final_state = env.state().model_dump()
    score = grade_episode(final_state)

    return {
        "difficulty": difficulty,
        "final_state": final_state,
        "score": score
    }


def main():
    difficulties = ["easy", "medium", "hard"]
    results = []

    print("=" * 60)
    print("Lifestyle Planner Baseline Evaluation")
    print("=" * 60)

    for difficulty in difficulties:
        result = run_baseline_for_difficulty(difficulty)
        results.append(result)

        print(f"\nDifficulty: {difficulty.upper()}")
        print(f"Completed Tasks: {result['final_state']['completed_tasks']}")
        print(f"Remaining Tasks: {[task['name'] for task in result['final_state']['tasks']]}")
        print(f"Total Reward: {result['final_state']['total_reward']}")
        print(f"Final Energy: {result['final_state']['energy_level']}")
        print(f"Score: {result['score']}")

    avg_score = round(sum(r["score"] for r in results) / len(results), 3)

    print("\n" + "=" * 60)
    print(f"Average Baseline Score: {avg_score}")
    print("=" * 60)


if __name__ == "__main__":
    main()
>>>>>>> 6d39c54215ae40124371e71bc5c5390de8d5fe7e
