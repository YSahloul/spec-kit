"""
OpenCode /research command implementation
"""

from typing import Optional, List
import typer

from specify_cli.services.research_engine import ResearchEngine


def research(
    topic: str = typer.Option(..., "--topic", "-t", help="Research topic"),
    sources: Optional[List[str]] = typer.Option(None, "--sources", "-s", help="Research sources"),
    spec_id: Optional[str] = typer.Option(None, "--spec-id", "-i", help="Associated specification ID")
) -> None:
    """Research technical topics

    This command conducts research on the specified topic using various sources
    and associates it with a specification if provided.
    """
    try:
        # Normalize sources
        if sources is None:
            sources = ["web"]

        # Conduct research
        research_engine = ResearchEngine()
        research_item = research_engine.conduct_research(
            topic=topic,
            sources=sources,
            spec_id=spec_id
        )

        # Display results
        typer.echo(f"✅ Research completed successfully!")
        typer.echo(f"   Topic: {research_item.topic}")
        typer.echo(f"   Sources: {research_item.source}")

        if research_item.decision:
            typer.echo(f"   Decision: {research_item.decision}")

        if research_item.alternatives:
            typer.echo(f"   Alternatives: {len(research_item.alternatives)}")

    except Exception as e:
        typer.echo(f"❌ Error conducting research: {str(e)}", err=True)
        raise typer.Exit(1)


def register_research_command(app: typer.Typer) -> None:
    """Register the /research command with the OpenCode CLI"""
    app.command("/research")(research)


if __name__ == "__main__":
    # For testing purposes
    typer.run(research)