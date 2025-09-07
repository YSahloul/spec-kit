"""
OpenCode /spec command implementation
"""

from typing import Optional
import typer
from pathlib import Path

from specify_cli.services.spec_generator import SpecGenerator


def create_spec(
    description: str = typer.Option(..., "--description", "-d", help="Feature description"),
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Template name to use"),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Custom branch name")
) -> None:
    """Create a new feature specification

    This command creates a new specification file with the given description,
    optionally using a template and custom branch name.
    """
    try:
        # Initialize spec generator
        generator = SpecGenerator()

        # Create specification
        spec = generator.create_spec(
            description=description,
            template_name=template,
            branch_name=branch
        )

        # Display results
        typer.echo(f"✅ Specification created successfully!")
        typer.echo(f"   ID: {spec.id}")
        typer.echo(f"   Branch: {spec.branch}")
        typer.echo(f"   Path: {spec.path}")
        typer.echo(f"   Status: {spec.status}")

        if template:
            typer.echo(f"   Template: {template}")

    except Exception as e:
        typer.echo(f"❌ Error creating specification: {str(e)}", err=True)
        raise typer.Exit(1)


def register_spec_command(app: typer.Typer) -> None:
    """Register the /spec command with the OpenCode CLI"""
    app.command("/spec")(create_spec)


if __name__ == "__main__":
    # For testing purposes
    typer.run(create_spec)