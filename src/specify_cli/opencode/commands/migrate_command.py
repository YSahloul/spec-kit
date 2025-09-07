"""
OpenCode /migrate command implementation
"""

from typing import Optional
import typer

from specify_cli.services.codebase_analyzer import CodebaseAnalyzer


def migrate_project(
    mode: str = typer.Option("incremental", "--mode", "-m", help="Migration mode"),
    preserve_structure: bool = typer.Option(True, "--preserve-structure/--no-preserve-structure", help="Preserve existing structure")
) -> None:
    """Migrate existing project to spec-driven

    This command analyzes an existing codebase and creates specifications
    to migrate it to a spec-driven development approach.
    """
    try:
        # Analyze current codebase
        analyzer = CodebaseAnalyzer()
        analysis_result = analyzer.analyze_codebase()

        if not analysis_result.get("migration_ready", False):
            typer.echo("❌ Codebase not ready for migration", err=True)
            typer.echo("   Run '/analyze' first to check migration readiness")
            raise typer.Exit(1)

        # Generate migration spec
        migration_spec = analyzer.generate_migration_spec(analysis_result)

        # Display results
        typer.echo(f"✅ Migration initiated successfully!")
        typer.echo(f"   Mode: {mode}")
        typer.echo(f"   Preserve Structure: {preserve_structure}")
        typer.echo(f"   Features Found: {analysis_result['features_found']}")

        if migration_spec:
            typer.echo(f"   Migration Spec Created: {migration_spec.get('title', 'Unknown')}")

    except Exception as e:
        typer.echo(f"❌ Error migrating project: {str(e)}", err=True)
        raise typer.Exit(1)


def register_migrate_command(app: typer.Typer) -> None:
    """Register the /migrate command with the OpenCode CLI"""
    app.command("/migrate")(migrate_project)


if __name__ == "__main__":
    # For testing purposes
    typer.run(migrate_project)