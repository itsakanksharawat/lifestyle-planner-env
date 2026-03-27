from models import LifestyleAction
from server.lifestyle_planner_environment import LifestylePlannerEnvironment


def dummy_agent(task_type, user_state):
    if task_type == "plan_day":
        return "Study in the evening, do a short workout, eat meals on time, and sleep before 11 PM."
    elif task_type == "recover_day":
        return "Prioritize the most important task, reduce screen time, take a short walk, and sleep early."
    elif task_type == "optimize_week":
        return "Create a weekly routine with study blocks, 4 workouts, consistent sleep, and fallback habit rules."
    return "Make a balanced lifestyle plan."


env = LifestylePlannerEnvironment()
obs = env.reset()

action = LifestyleAction(
    action_type=obs.task_type,
    plan=dummy_agent(obs.task_type, obs.user_state)
)

observation, reward, done, info = env.step(action)

print("Task:", obs.task_type)
print("Instruction:", obs.instruction)
print("Plan:", action.plan)
print("Reward:", reward)
print("Done:", done)
print("Info:", info)
print("State:", env.state())