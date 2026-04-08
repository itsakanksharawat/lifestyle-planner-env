from fastapi import Body

@app.post("/reset", response_model=ResetResponse)
def reset(req: Optional[ResetRequest] = Body(default=None)):
    """Start a new episode. Works even without request body."""

    task_type = req.task_type if req else None
    difficulty = req.difficulty if req else None

    if task_type and task_type not in TASK_TYPES:
        raise HTTPException(400, f"Invalid task_type. Choose from: {TASK_TYPES}")
    if difficulty and difficulty not in DIFFICULTY_LEVELS:
        raise HTTPException(400, f"Invalid difficulty. Choose from: {DIFFICULTY_LEVELS}")

    env = LifestylePlannerEnvironment()
    obs = env.reset(task_type=task_type, difficulty=difficulty)
    episode_id = env.state().episode_id
    _sessions[episode_id] = env

    return ResetResponse(episode_id=episode_id, observation=obs)