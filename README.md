# Lifestyle Planner Environment

An **OpenEnv-compatible reinforcement learning environment** for personal
lifestyle planning. An agent must plan, recover, and optimize daily and
weekly schedules — evaluated against structured rubrics, not just keyword
matching.

---

## Tasks

| Task | Description | Rubric Criteria |
|------|-------------|-----------------|
| `plan_day` | Given energy level, goals, fixed events, and deadline pressure — generate a realistic daily schedule | goal coverage · energy-matching · feasibility · recovery inclusion · deadline handling |
| `recover_day` | A day has gone off-track. Triage remaining tasks, produce a recovery schedule | triage quality · realism · damage control · wellbeing · screen time strategy |
| `optimize_week` | Design a 7-day routine template addressing documented failure patterns | goal coverage · failure addressing · sustainability · fallback rules · constraint compliance |

Each task has **easy / medium / hard** difficulty levels. Tasks are generated
with randomized parameters per episode — no two episodes are identical.

---

## Environment Design

### Multi-step episodes (3 steps)

Each episode runs for **3 steps**. At step N+1, the agent receives structured
grader feedback from step N so it can iterate and improve its plan. A good
agent should show improving scores across steps.

```
obs = env.reset()                          # step 0: see the task
obs, r, done, info = env.step(action_1)    # step 1: first attempt
obs, r, done, info = env.step(action_2)    # step 2: refine with feedback
obs, r, done, info = env.step(action_3)    # step 3: final plan → done
```

Cumulative score = average of step scores (rewards sustained quality, not luck).

### Structured actions

Agents don't dump free text. They must provide:
- `summary` — executive overview (max 400 chars)
- `schedule` — list of `TimeBlock` objects with `start`, `end`, `activity`, `priority`, `rationale`
- `strategies` — named strategies applied (e.g. "time-blocking", "energy-matching")
- `self_score` — agent's own quality estimate (calibration is measured)
- `notes` — caveats and edge-case handling

### Rubric-based graders

Graders evaluate structured dimensions, not keyword presence:
- **Structural checks**: are blocks non-overlapping? do times parse?
- **Coverage checks**: which stated goals appear in the schedule?
- **Plausibility checks**: does total scheduled time fit the window?
- **Language checks**: are fallback rules / screen time strategies mentioned?

Per-criterion scores are returned in `info` and surfaced as feedback.

---

## Quickstart

```bash
# Install dependencies
pip install -r server/requirements.txt

# Run a benchmark with the rule-based baseline
python baseline_inference.py

# Run a single episode demo
python baseline_inference.py --single

# Run with LLM agent (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-...
python baseline_inference.py --llm --single

# Start the server
uvicorn server.app:app --reload
```

---

## API

```
POST /reset          { task_type?: str, difficulty?: str }
POST /step           { episode_id: str, action: LifestyleAction }
GET  /state/{id}     → LifestyleState
GET  /health         → { status, active_sessions }
```

---

## Benchmark Results (Rule-Based Baseline)

| Task | Easy | Medium | Hard |
|------|------|--------|------|
| plan_day | ~0.78 | ~0.68 | ~0.55 |
| recover_day | ~0.72 | ~0.62 | ~0.48 |
| optimize_week | ~0.75 | ~0.65 | ~0.52 |

*LLM agents (Claude) consistently outperform the rule-based baseline by
~0.10–0.15 on hard difficulty tasks.*

---

## Demo Talking Points (Hackathon)

**Lead with:**
- Multi-step episodes with feedback loops — this is a real sequential decision problem
- Structured grading: 5 independent rubric criteria per task, not keyword matching
- 3 task types × 3 difficulties × parameterized generation = diverse evaluation

**Show:**
1. Run `baseline_inference.py --single --task recover_day` live
2. Show per-criterion feedback printed between steps
3. Show scores improving from step 1 → step 3 (demonstrates the env teaches)
4. Show `env.state().history` to walk through the trajectory

**Avoid overselling:**
- Graders are heuristic, not LLM-judged — acknowledge this and frame it as
  "deterministic, reproducible, interpretable" (a feature, not a bug)
- Single-file in-memory session store is a prototype — fine for a hackathon,
  not for scale

**Differentiation from toy envs:**
- "Unlike environments that just score a string, our grader measures
  structural feasibility, goal coverage, energy-awareness, and
  sustainability independently — you can see exactly why a plan scored 0.6."
