"""
TaskManager service
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from specify_cli.models.task import Task
from specify_cli.models.implementation_plan import ImplementationPlan


class TaskManager:
    """Service for managing tasks"""

    def __init__(self, base_path: str = "."):
        self.base_path = base_path
        self.tasks: Dict[str, Task] = {}

    def create_tasks_from_plan(self, plan: ImplementationPlan, grouping: str = "hybrid") -> List[Task]:
        """Create tasks from an implementation plan"""
        tasks = []

        # Generate tasks based on plan phases
        for phase in plan.phases:
            phase_tasks = self._generate_tasks_for_phase(phase, plan.spec_id)
            tasks.extend(phase_tasks)

        # Set up dependencies based on grouping strategy
        if grouping == "sequential":
            self._setup_sequential_dependencies(tasks)
        elif grouping == "parallel":
            self._setup_parallel_dependencies(tasks)
        else:  # hybrid
            self._setup_hybrid_dependencies(tasks)

        # Store tasks
        for task in tasks:
            self.tasks[task.id] = task

        return tasks

    def _generate_tasks_for_phase(self, phase: Dict[str, Any], spec_id: str) -> List[Task]:
        """Generate tasks for a specific phase"""
        tasks = []
        phase_name = phase["name"]

        # Create tasks based on phase artifacts
        for i, artifact in enumerate(phase["artifacts"]):
            task = Task(
                id=f"{spec_id}-{phase_name}-{i+1}",
                content=f"Implement {artifact} for {phase_name} phase",
                plan_id=spec_id
            )
            tasks.append(task)

        return tasks

    def _setup_sequential_dependencies(self, tasks: List[Task]) -> None:
        """Set up sequential dependencies (one after another)"""
        for i in range(1, len(tasks)):
            tasks[i].add_dependency(tasks[i-1].id)

    def _setup_parallel_dependencies(self, tasks: List[Task]) -> None:
        """Set up parallel dependencies (no dependencies)"""
        # No dependencies for parallel execution
        pass

    def _setup_hybrid_dependencies(self, tasks: List[Task]) -> None:
        """Set up hybrid dependencies (some parallel, some sequential)"""
        # Group tasks by phase and make phases sequential
        phase_groups = {}
        for task in tasks:
            phase = task.id.split('-')[1]  # Extract phase from task ID
            if phase not in phase_groups:
                phase_groups[phase] = []
            phase_groups[phase].append(task)

        # Make phases sequential
        phases = list(phase_groups.keys())
        for i in range(1, len(phases)):
            current_phase_tasks = phase_groups[phases[i]]
            previous_phase_tasks = phase_groups[phases[i-1]]

            # Make first task of current phase depend on last task of previous phase
            if current_phase_tasks and previous_phase_tasks:
                current_phase_tasks[0].add_dependency(previous_phase_tasks[-1].id)

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)

    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        task = self.get_task(task_id)
        if not task:
            return False

        task.update_status(status)
        return True

    def get_pending_tasks(self, plan_id: Optional[str] = None) -> List[Task]:
        """Get all pending tasks, optionally filtered by plan"""
        tasks = [task for task in self.tasks.values() if task.is_pending]
        if plan_id:
            tasks = [task for task in tasks if task.plan_id == plan_id]
        return tasks

    def get_completed_tasks(self, plan_id: Optional[str] = None) -> List[Task]:
        """Get all completed tasks, optionally filtered by plan"""
        tasks = [task for task in self.tasks.values() if task.is_completed]
        if plan_id:
            tasks = [task for task in tasks if task.plan_id == plan_id]
        return tasks

    def can_start_task(self, task_id: str) -> bool:
        """Check if a task can be started"""
        task = self.get_task(task_id)
        if not task:
            return False

        return task.can_start()

    def get_next_executable_tasks(self, plan_id: Optional[str] = None) -> List[Task]:
        """Get tasks that can be executed next"""
        pending_tasks = self.get_pending_tasks(plan_id)
        return [task for task in pending_tasks if task.can_start()]

    def get_task_summary(self, plan_id: Optional[str] = None) -> Dict[str, int]:
        """Get task summary statistics"""
        all_tasks = list(self.tasks.values())
        if plan_id:
            all_tasks = [task for task in all_tasks if task.plan_id == plan_id]

        return {
            "total": len(all_tasks),
            "pending": len([t for t in all_tasks if t.is_pending]),
            "in_progress": len([t for t in all_tasks if t.is_in_progress]),
            "completed": len([t for t in all_tasks if t.is_completed]),
            "cancelled": len([t for t in all_tasks if t.is_cancelled])
        }