from fastapi import FastAPI
from lifestyle_planner_env.models import LifestyleAction
from lifestyle_planner_env.server.lifestyle_planner_environment import LifestylePlannerEnv

app = FastAPI(title="Lifestyle Planner OpenEnv")

env = LifestylePlannerEnv()


@app.get("/")
def home():
    return {"message": "Lifestyle Planner OpenEnv is running"}


@app.post("/reset")
def reset():
    return env.reset()


@app.get("/state")
def state():
    return env.state()


@app.post("/step")
def step(action: LifestyleAction):
    return env.step(action)