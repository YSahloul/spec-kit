"""
OpenCode /tasks command implementation
"""

from typing import Optional
import typer

from specify_cli.services.task_manager import TaskManager
from specify_cli.services.plan_builder import PlanBuilder
from specify_cli.services.spec_generator import SpecGenerator


def create_tasks(
    plan_id: Optional[str] = typer.Option(None, "--plan-id", "-p", help="Plan ID (defaults to current)"),
    grouping: str = typer.Option("hybrid", "--grouping", "-g", help="Task grouping strategy")
) -> None:
    """Generate task list from implementation plan

    This command creates a task breakdown from the current plan
    or a specified plan ID, with configurable grouping strategy.
    """
    try:
        # Get plan
        if plan_id:
            plan_builder = PlanBuilder()
            plan = plan_builder.get_plan(plan_id)
            if not plan:
                typer.echo(f"❌ Plan '{plan_id}' not found", err=True)
                raise typer.Exit(1)
        else:
            # Find current plan (simplified - would need better logic)
            typer.echo("❌ No plan ID provided and no current plan found", err=True)
            raise typer.Exit(1)

        # Create tasks
        task_manager = TaskManager()
        tasks = task_manager.create_tasks_from_plan(plan, grouping)

        # Display results
        typer.echo(f"✅ Task list created successfully!")
        typer.echo(f"   Plan ID: {plan.spec_id}")
        typer.echo(f"   Tasks Created: {len(tasks)}")
        typer.echo(f"   Grouping: {grouping}")

        # Show task summary
        summary = task_manager.get_task_summary(plan.spec_id)
        typer.echo(f"   Pending: {summary['pending']}")
        typer.echo(f"   In Progress: {summary['in_progress']}")
        typer.echo(f"   Completed: {summary['completed']}")

    except Exception as e:
        typer.echo(f"❌ Error creating tasks: {str(e)}", err=True)
        raise typer.Exit(1)


def register_tasks_command(app: typer.Typer) -> None:
    """Register the /tasks command with the OpenCode CLI"""
    app.command("/tasks")(create_tasks)


if __name__ == "__main__":
    # For testing purposes
    typer.run(create_tasks)