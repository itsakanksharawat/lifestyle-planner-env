from lifestyle_planner_env.models import (
    LifestyleAction,
    LifestyleObservation,
    LifestyleState,
    LifestyleTask,
    StepResult
)


class LifestylePlannerEnv:
    def __init__(self):
        self.reset()

    def reset(self):
        self.current_time = 0
        self.max_time = 8
        self.energy_level = 10
        self.total_reward = 0.0

        self.tasks = [
            LifestyleTask(name="Study", priority=5, duration=3, deadline=4),
            LifestyleTask(name="Workout", priority=4, duration=2, deadline=6),
            LifestyleTask(name="Assignment", priority=6, duration=2, deadline=3),
        ]

        self.completed_tasks = []

        return self.state()

    def state(self):
        return LifestyleState(
            current_time=self.current_time,
            max_time=self.max_time,
            energy_level=self.energy_level,
            tasks=self.tasks,
            completed_tasks=self.completed_tasks,
            total_reward=self.total_reward
        )

    def step(self, action: LifestyleAction):
        self.current_time += 1
        reward = 0.0

        chosen_task = next(
            (task for task in self.tasks if task.name == action.task_name),
            None
        )

        if chosen_task:
            chosen_task.duration -= 1
            self.energy_level -= 1
            reward += chosen_task.priority * 0.5

            if chosen_task.duration <= 0:
                self.completed_tasks.append(chosen_task.name)
                self.tasks.remove(chosen_task)
                reward += chosen_task.priority * 2
        else:
            reward -= 2.0  # invalid or wasted action

        # deadline penalties
        for task in self.tasks:
            if self.current_time > task.deadline:
                reward -= task.priority * 1.0

        # burnout penalty
        if self.energy_level <= 2:
            reward -= 3.0

        self.total_reward += reward
        done = self.current_time >= self.max_time or len(self.tasks) == 0

        observation = LifestyleObservation(
            current_time=self.current_time,
            max_time=self.max_time,
            energy_level=self.energy_level,
            tasks=self.tasks,
            completed_tasks=self.completed_tasks
        )

        return StepResult(
            observation=observation,
            reward=reward,
            done=done,
            info={"total_reward": self.total_reward}
        )
    