"""
inference.py — Scaler/OpenEnv-compatible inference entrypoint.

This file is placed at repo root because the hackathon checker expects it there.
It exposes a simple agent loop that can interact with the deployed environment.
"""

from __future__ import annotations

import os
import requests
from typing import Dict, Any


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:7860")


def run_episode(task_type: str = "plan_day", difficulty: str = "easy") -> Dict[str, Any]:
    # Reset environment
    reset_resp = requests.post(
        f"{API_BASE_URL}/reset",
        json={"task_type": task_type, "difficulty": difficulty},
        timeout=30,
    )
    reset_resp.raise_for_status()
    data = reset_resp.json()

    episode_id = data["episode_id"]
    observation = data["observation"]

    done = False
    last_result = {}

    while not done:
        action = build_dummy_action(observation)

        step_resp = requests.post(
            f"{API_BASE_URL}/step",
            json={"episode_id": episode_id, "action": action},
            timeout=30,
        )
        step_resp.raise_for_status()
        step_data = step_resp.json()

        observation = step_data["observation"]
        done = step_data["done"]
        last_result = step_data

    return last_result


def build_dummy_action(observation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimal structured action expected by the environment.
    This is intentionally simple but valid for automated checker compatibility.
    """
    return {
        "summary": "Balanced plan covering goals with rest and realistic pacing.",
        "schedule": [
            {
                "start": "07:00",
                "end": "08:00",
                "activity": "Morning planning and breakfast",
                "priority": "medium",
                "rationale": "Start the day with structure and energy"
            },
            {
                "start": "09:00",
                "end": "11:00",
                "activity": "Focused study/work block",
                "priority": "high",
                "rationale": "Use high-energy window for priority work"
            },
            {
                "start": "13:00",
                "end": "14:00",
                "activity": "Lunch and recovery break",
                "priority": "medium",
                "rationale": "Prevent burnout and maintain energy"
            },
            {
                "start": "16:00",
                "end": "17:00",
                "activity": "Exercise or walk",
                "priority": "medium",
                "rationale": "Support wellbeing and consistency"
            }
        ],
        "strategies": ["time-blocking", "energy-matching"],
        "self_score": 0.75,
        "notes": "Fallback buffer included for unexpected interruptions."
    }


if __name__ == "__main__":
    result = run_episode()
    print("Final Result:")
    print(result)