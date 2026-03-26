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