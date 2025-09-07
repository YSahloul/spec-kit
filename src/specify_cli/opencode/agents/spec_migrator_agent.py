"""
Spec-migrator agent implementation
"""

from typing import Dict, Any, Optional
from datetime import datetime

from specify_cli.services.codebase_analyzer import CodebaseAnalyzer


class SpecMigratorAgent:
    """Agent for migrating projects to spec-driven development"""

    def __init__(self):
        self.analyzer = CodebaseAnalyzer()
        self.name = "spec-migrator"
        self.capabilities = ["migrate_project", "analyze_structure", "generate_migration_plan"]

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute migration task"""
        action = input_data.get("action", "migrate")

        if action == "migrate":
            return self._migrate_project(input_data)
        elif action == "analyze":
            return self._analyze_structure(input_data)
        elif action == "plan":
            return self._generate_migration_plan(input_data)
        else:
            return {
                "error": f"Unknown action: {action}",
                "supported_actions": self.capabilities
            }

    def _migrate_project(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate a project to spec-driven development"""
        mode = input_data.get("mode", "incremental")
        preserve_structure = input_data.get("preserve_structure", True)

        try:
            # Analyze the current codebase
            analysis_result = self.analyzer.analyze_codebase()

            if not analysis_result.get("migration_ready", False):
                return {
                    "error": "Project not ready for migration",
                    "issues": analysis_result.get("recommendations", [])
                }

            # Generate migration specification
            migration_spec = self.analyzer.generate_migration_spec(analysis_result)

            return {
                "success": True,
                "mode": mode,
                "preserve_structure": preserve_structure,
                "migration_spec": migration_spec,
                "analysis": analysis_result
            }
        except Exception as e:
            return {"error": f"Failed to migrate project: {str(e)}"}

    def _analyze_structure(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project structure for migration"""
        path = input_data.get("path", ".")

        try:
            analysis_result = self.analyzer.analyze_codebase(path=path)

            structure_analysis = {
                "directories": analysis_result["structure"]["directories"],
                "files": analysis_result["structure"]["files"],
                "languages": list(analysis_result["structure"]["languages"].keys()),
                "migration_complexity": "low" if analysis_result["features_found"] < 5 else "medium" if analysis_result["features_found"] < 15 else "high"
            }

            return {
                "success": True,
                "structure_analysis": structure_analysis,
                "recommendations": analysis_result["recommendations"]
            }
        except Exception as e:
            return {"error": f"Failed to analyze structure: {str(e)}"}

    def _generate_migration_plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed migration plan"""
        analysis_result = input_data.get("analysis_result")
        if not analysis_result:
            return {"error": "Analysis result is required for migration plan"}

        try:
            # Create migration plan based on analysis
            migration_plan = {
                "title": "Project Migration Plan",
                "phases": [
                    {
                        "name": "analysis",
                        "status": "completed",
                        "tasks": ["Analyze codebase structure", "Identify features"]
                    },
                    {
                        "name": "planning",
                        "status": "in_progress",
                        "tasks": ["Create migration specifications", "Plan implementation phases"]
                    },
                    {
                        "name": "implementation",
                        "status": "pending",
                        "tasks": ["Set up spec-kit", "Create initial specifications"]
                    },
                    {
                        "name": "validation",
                        "status": "pending",
                        "tasks": ["Test migration", "Validate specifications"]
                    }
                ],
                "estimated_effort": f"{analysis_result['features_found'] * 2} hours",
                "risk_level": "low" if analysis_result["migration_ready"] else "medium"
            }

            return {
                "success": True,
                "migration_plan": migration_plan
            }
        except Exception as e:
            return {"error": f"Failed to generate migration plan: {str(e)}"}

    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "name": self.name,
            "status": "active",
            "capabilities": self.capabilities,
            "last_active": datetime.now().isoformat()
        }

    def get_capabilities(self) -> list[str]:
        """Get agent capabilities"""
        return self.capabilities.copy()