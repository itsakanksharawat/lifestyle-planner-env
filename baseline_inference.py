from lifestyle_planner_env.server.lifestyle_planner_environment import LifestylePlannerEnv
from lifestyle_planner_env.models import LifestyleAction
from lifestyle_planner_env.graders import grade_episode


def choose_action(observation):
    """
    Simple heuristic baseline:
    choose task by urgency-adjusted priority
    """

    if not observation.tasks:
        return None

    def task_score(task):
        urgency = max(1, task.deadline - observation.current_time)
        return (task.priority / max(1, task.duration)) + (1 / urgency)

    best_task = max(observation.tasks, key=task_score)
    return LifestyleAction(task_name=best_task.name)


def run_baseline_for_difficulty(difficulty: str):
    env = LifestylePlannerEnv(difficulty=difficulty)
    obs = env.reset()

    done = False

    while not done:
        action = choose_action(obs)
        if action is None:
            break

        result = env.step(action)
        obs = result.observation
        done = result.done

    final_state = env.state().model_dump()
    score = grade_episode(final_state)

    return {
        "difficulty": difficulty,
        "final_state": final_state,
        "score": score
    }


def main():
    difficulties = ["easy", "medium", "hard"]
    results = []

    print("=" * 60)
    print("Lifestyle Planner Baseline Evaluation")
    print("=" * 60)

    for difficulty in difficulties:
        result = run_baseline_for_difficulty(difficulty)
        results.append(result)

        print(f"\nDifficulty: {difficulty.upper()}")
        print(f"Completed Tasks: {result['final_state']['completed_tasks']}")
        print(f"Remaining Tasks: {[task['name'] for task in result['final_state']['tasks']]}")
        print(f"Total Reward: {result['final_state']['total_reward']}")
        print(f"Final Energy: {result['final_state']['energy_level']}")
        print(f"Score: {result['score']}")

    avg_score = round(sum(r["score"] for r in results) / len(results), 3)

    print("\n" + "=" * 60)
    print(f"Average Baseline Score: {avg_score}")
    print("=" * 60)


if __name__ == "__main__":
    main()