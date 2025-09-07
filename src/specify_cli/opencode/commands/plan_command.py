"""
OpenCode /plan command implementation
"""

from typing import Optional
import typer

from specify_cli.services.plan_builder import PlanBuilder
from specify_cli.services.spec_generator import SpecGenerator


def create_plan(
    spec_id: Optional[str] = typer.Option(None, "--spec-id", "-s", help="Specification ID (defaults to current)"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Programming language"),
    framework: Optional[str] = typer.Option(None, "--framework", "-f", help="Framework to use")
) -> None:
    """Generate implementation plan for current specification

    This command creates an implementation plan based on the current specification
    or a specified spec ID, with optional technical context.
    """
    try:
        # Get specification
        if spec_id:
            spec_generator = SpecGenerator()
            spec = spec_generator.get_spec(spec_id)
            if not spec:
                typer.echo(f"❌ Specification '{spec_id}' not found", err=True)
                raise typer.Exit(1)
        else:
            # Find current spec (simplified - would need better logic)
            typer.echo("❌ No spec ID provided and no current spec found", err=True)
            raise typer.Exit(1)

        # Build technical context
        technical_context = {}
        if language:
            technical_context["language"] = language
        if framework:
            technical_context["framework"] = framework

        # Create plan
        plan_builder = PlanBuilder()
        plan = plan_builder.create_plan(spec, technical_context)

        # Display results
        typer.echo(f"✅ Implementation plan created successfully!")
        typer.echo(f"   Spec ID: {plan.spec_id}")
        typer.echo(f"   Path: {plan.path}")
        typer.echo(f"   Phases: {len(plan.phases)}")

        if technical_context:
            typer.echo(f"   Technical Context: {technical_context}")

    except Exception as e:
        typer.echo(f"❌ Error creating plan: {str(e)}", err=True)
        raise typer.Exit(1)


def register_plan_command(app: typer.Typer) -> None:
    """Register the /plan command with the OpenCode CLI"""
    app.command("/plan")(create_plan)


if __name__ == "__main__":
    # For testing purposes
    typer.run(create_plan)