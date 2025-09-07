"""
OpenCode /analyze command implementation
"""

from typing import Optional
import typer

from specify_cli.services.codebase_analyzer import CodebaseAnalyzer


def analyze_codebase(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Path to analyze (defaults to current)"),
    depth: str = typer.Option("deep", "--depth", "-d", help="Analysis depth")
) -> None:
    """Analyze existing codebase

    This command analyzes an existing codebase to identify features,
    structure, and generate migration recommendations.
    """
    try:
        # Analyze codebase
        analyzer = CodebaseAnalyzer()
        analysis_result = analyzer.analyze_codebase(path=path, depth=depth)

        # Display results
        typer.echo(f"✅ Codebase analysis completed!")
        typer.echo(f"   Features Found: {analysis_result['features_found']}")
        typer.echo(f"   Migration Ready: {analysis_result['migration_ready']}")

        structure = analysis_result.get("structure", {})
        typer.echo(f"   Directories: {structure.get('directories', 0)}")
        typer.echo(f"   Files: {structure.get('files', 0)}")

        recommendations = analysis_result.get("recommendations", [])
        if recommendations:
            typer.echo(f"   Recommendations: {len(recommendations)}")
            for rec in recommendations[:3]:  # Show first 3
                typer.echo(f"     - {rec}")

    except Exception as e:
        typer.echo(f"❌ Error analyzing codebase: {str(e)}", err=True)
        raise typer.Exit(1)


def register_analyze_command(app: typer.Typer) -> None:
    """Register the /analyze command with the OpenCode CLI"""
    app.command("/analyze")(analyze_codebase)


if __name__ == "__main__":
    # For testing purposes
    typer.run(analyze_codebase)