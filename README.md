---
title: Lifestyle Planner Env
emoji: 🧠
colorFrom: blue
colorTo: purple
sdk: docker
app_file: server/app.py
pinned: false
---

# Lifestyle Planner Environment

An OpenEnv-compatible reinforcement learning environment for personal lifestyle planning.

## Tasks

- **plan_day** → Generate a realistic daily schedule  
- **recover_day** → Recover from a disrupted day  
- **optimize_week** → Design a sustainable weekly routine  

## Features

- Multi-step episodes (3-step refinement loop)
- Structured action space (not just text)
- Rubric-based grading (feasibility, goals, energy, recovery)
- Deterministic evaluation (not black-box LLM grading)

## Quickstart

```bash
pip install -r server/requirements.txt
uvicorn server.app:app --reload