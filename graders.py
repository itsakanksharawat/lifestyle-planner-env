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