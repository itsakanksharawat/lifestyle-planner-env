# Lifestyle Planner Env

Lifestyle Planner Env is an OpenEnv-style agentic environment that simulates real-world personal lifestyle management tasks.

## What it does
This environment allows an AI agent to:
- Plan a realistic day
- Recover a broken day
- Optimize a weekly routine

## Tasks
1. **Plan a Realistic Day**
2. **Recover a Broken Day**
3. **Optimize Weekly Routine**

## Core APIs
- `reset()`
- `step(action)`
- `state()`

## Project Structure
- `task_bank.py` → Task definitions
- `models.py` → Observation, Action, State
- `graders.py` → Task scoring logic
- `server/lifestyle_planner_environment.py` → Environment logic
- `baseline_inference.py` → Demo baseline run

## How to run

Install dependencies:

```bash
pip install fastapi uvicorn pydantic