"""
Spec-analyzer agent implementation
"""

# @v Provide intelligent analysis of codebases to generate migration-ready specifications
# @context This agent bridges the gap between raw code analysis and structured migration planning
# @a Initialize analyzer with core capabilities for spec generation
# test 
from typing import Dict, Any, Optional
from datetime import datetime

from specify_cli.services.codebase_analyzer import CodebaseAnalyzer


class SpecAnalyzerAgent:
    """Agent for analyzing specifications and codebases"""

    def __init__(self):
        # @a Set up core analyzer service and agent identity
        self.analyzer = CodebaseAnalyzer()
        self.name = "spec-analyzer"
        self.capabilities = ["analyze_codebase", "generate_specs", "validate_structure"]

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis task"""
        # @a Route incoming requests to appropriate analysis methods
        # @q Should we add more action types for different analysis depths?
        action = input_data.get("action", "analyze")

        if action == "analyze":
            return self._analyze_codebase(input_data)
        elif action == "generate":
            return self._generate_specs(input_data)
        elif action == "validate":
            return self._validate_structure(input_data)
        else:
            # @issue Handle unknown actions gracefully with helpful error messages
            return {
                "error": f"Unknown action: {action}",
                "supported_actions": self.capabilities
            }

    def _analyze_codebase(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a codebase"""
        # @a Extract analysis parameters and perform deep codebase inspection
        # @context This method handles the core analysis workflow
        path = input_data.get("path")
        depth = input_data.get("depth", "deep")

        try:
            # @insight Use analyzer service to get comprehensive codebase understanding
            analysis_result = self.analyzer.analyze_codebase(path=path, depth=depth)

            return {
                "success": True,
                "features_found": analysis_result["features_found"],
                "migration_ready": analysis_result["migration_ready"],
                "structure": analysis_result["structure"],
                "recommendations": analysis_result["recommendations"]
            }
        except Exception as e:
            # @bug Handle analysis failures with descriptive error messages
            return {"error": f"Failed to analyze codebase: {str(e)}"}

    def _generate_specs(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specifications from analysis"""
        # @a Transform raw analysis data into structured migration specifications
        # @prereq Requires completed codebase analysis as input
        analysis_result = input_data.get("analysis_result")
        if not analysis_result:
            return {"error": "Analysis result is required for spec generation"}

        try:
            # @a Use analyzer to create migration-ready specifications
            migration_spec = self.analyzer.generate_migration_spec(analysis_result)

            if migration_spec:
                return {
                    "success": True,
                    "spec_title": migration_spec.get("title", "Generated Spec"),
                    "recommendations": migration_spec.get("recommendations", [])
                }
            else:
                # @issue Spec generation failed - investigate analyzer implementation
                return {"error": "Failed to generate migration specification"}
        except Exception as e:
            # @bug Handle spec generation errors gracefully
            return {"error": f"Failed to generate specs: {str(e)}"}

    def _validate_structure(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate project structure"""
        # @a Perform lightweight validation of project structure and readiness
        # @test Validate that project has minimum requirements for migration
        path = input_data.get("path", ".")

        try:
            # @a Quick shallow analysis to check project health
            analysis_result = self.analyzer.analyze_codebase(path=path, depth="shallow")

            validation = {
                "has_structure": analysis_result["structure"]["directories"] > 0,
                "has_files": analysis_result["structure"]["files"] > 0,
                "migration_ready": analysis_result["migration_ready"],
                "issues": []
            }

            # @a Check for common validation issues
            if analysis_result["structure"]["files"] == 0:
                validation["issues"].append("No files found in project")
            if analysis_result["features_found"] == 0:
                validation["issues"].append("No recognizable features found")

            return {
                "success": True,
                "validation": validation
            }
        except Exception as e:
            # @bug Handle validation failures with clear error reporting
            return {"error": f"Failed to validate structure: {str(e)}"}

    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        # @a Report current agent state and activity information
        return {
            "name": self.name,
            "status": "active",
            "capabilities": self.capabilities,
            "last_active": datetime.now().isoformat()
        }

    def get_capabilities(self) -> list[str]:
        """Get agent capabilities"""
        # @a Return list of supported analysis operations
        # @insight These capabilities define the agent's core functionality
        return self.capabilities.copy()