"""
server/app.py — FastAPI server exposing the Lifestyle Planner Environment.

Routes follow the OpenEnv convention:
    POST /reset           → start new episode, returns observation
    POST /step            → advance episode, returns (obs, reward, done, info)
    GET  /state/{id}      → return current episode state
    GET  /health          → liveness probe
    GET  /                → basic API info

Sessions are keyed by episode_id, stored in a simple in-memory dict.
For production, replace with Redis or a proper session store.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import LifestyleAction, LifestyleObservation, LifestyleState
from server.lifestyle_planner_environment import LifestylePlannerEnvironment
from task_bank import DIFFICULTY_LEVELS, TASK_TYPES

app = FastAPI(
    title="Lifestyle Planner Environment",
    description="OpenEnv-compatible RL environment for lifestyle planning tasks.",
    version="1.0.0",
)

# Enable CORS so frontend can call backend from browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # okay for local demo / hackathon
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store: episode_id → environment instance
_sessions: Dict[str, LifestylePlannerEnvironment] = {}


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    task_type: Optional[str] = None
    difficulty: Optional[str] = None


class ResetResponse(BaseModel):
    episode_id: str
    observation: LifestyleObservation


class StepRequest(BaseModel):
    episode_id: str
    action: LifestyleAction


class StepResponse(BaseModel):
    observation: LifestyleObservation
    reward: float
    done: bool
    info: Dict[str, Any]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Lifestyle Planner Environment API is running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
def health():
    return {"status": "ok", "active_sessions": len(_sessions)}


@app.post("/reset", response_model=ResetResponse)
def reset(req: ResetRequest):
    """Start a new episode. Returns the initial observation and episode_id."""
    if req.task_type and req.task_type not in TASK_TYPES:
        raise HTTPException(400, f"Invalid task_type. Choose from: {TASK_TYPES}")
    if req.difficulty and req.difficulty not in DIFFICULTY_LEVELS:
        raise HTTPException(400, f"Invalid difficulty. Choose from: {DIFFICULTY_LEVELS}")

    env = LifestylePlannerEnvironment()
    obs = env.reset(task_type=req.task_type, difficulty=req.difficulty)
    episode_id = env.state().episode_id
    _sessions[episode_id] = env

    return ResetResponse(episode_id=episode_id, observation=obs)


@app.post("/step", response_model=StepResponse)
def step(req: StepRequest):
    """Advance an episode by one step."""
    env = _sessions.get(req.episode_id)
    if env is None:
        raise HTTPException(404, f"Episode '{req.episode_id}' not found. Call /reset first.")

    try:
        obs, reward, done, info = env.step(req.action)
    except RuntimeError as e:
        raise HTTPException(400, str(e))

    if done:
        # Clean up session on episode completion
        del _sessions[req.episode_id]

    return StepResponse(observation=obs, reward=reward, done=done, info=info)


@app.get("/state/{episode_id}", response_model=LifestyleState)
def state(episode_id: str):
    """Return current state of an active episode."""
    env = _sessions.get(episode_id)
    if env is None:
        raise HTTPException(404, f"Episode '{episode_id}' not found.")
    return env.state()