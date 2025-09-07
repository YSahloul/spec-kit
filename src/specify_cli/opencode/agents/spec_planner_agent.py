"""
Spec-planner agent implementation
"""

from typing import Dict, Any, Optional
from datetime import datetime

from specify_cli.services.plan_builder import PlanBuilder
from specify_cli.services.spec_generator import SpecGenerator


class SpecPlannerAgent:
    """Agent for planning specifications - OpenCode compatible"""

    def __init__(self):
        self.plan_builder = PlanBuilder()
        self.spec_generator = SpecGenerator()
        self.name = "spec-planner"
        self.description = "Creates and manages implementation plans for specifications"
        self.version = "1.0.0"
        self.author = "spec-kit"
        self.capabilities = ["create_plan", "validate_plan", "update_plan"]
        self.supported_actions = ["create", "validate", "update"]
        self.metadata = {
            "category": "planning",
            "tags": ["plan", "implementation", "task"],
            "requires_project": True,
            "input_schema": {
                "create": {
                    "spec_id": {"type": "string", "required": True},
                    "technical_context": {"type": "object", "required": False}
                },
                "validate": {
                    "spec_id": {"type": "string", "required": True}
                },
                "update": {
                    "spec_id": {"type": "string", "required": True},
                    "phase_updates": {"type": "array", "required": False}
                }
            }
        }

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute planning task"""
        action = input_data.get("action", "create")

        if action == "create":
            return self._create_plan(input_data)
        elif action == "validate":
            return self._validate_plan(input_data)
        elif action == "update":
            return self._update_plan(input_data)
        else:
            return {
                "error": f"Unknown action: {action}",
                "supported_actions": self.capabilities
            }

    def _create_plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an implementation plan"""
        spec_id = input_data.get("spec_id")
        if not spec_id:
            return {"error": "spec_id is required for plan creation"}

        spec = self.spec_generator.get_spec(spec_id)
        if not spec:
            return {"error": f"Specification '{spec_id}' not found"}

        technical_context = input_data.get("technical_context", {})

        try:
            plan = self.plan_builder.create_plan(spec, technical_context)

            return {
                "success": True,
                "spec_id": plan.spec_id,
                "path": plan.path,
                "phases": len(plan.phases),
                "technical_context": plan.technical_context
            }
        except Exception as e:
            return {"error": f"Failed to create plan: {str(e)}"}

    def _validate_plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an existing plan"""
        spec_id = input_data.get("spec_id")
        if not spec_id:
            return {"error": "spec_id is required for plan validation"}

        plan = self.plan_builder.get_plan(spec_id)
        if not plan:
            return {"error": f"Plan for spec '{spec_id}' not found"}

        # Basic validation
        validation_results = {
            "has_spec_id": bool(plan.spec_id),
            "has_path": bool(plan.path),
            "has_phases": len(plan.phases) > 0,
            "phases_have_status": all(phase.get("status") for phase in plan.phases)
        }

        is_valid = all(validation_results.values())

        return {
            "spec_id": spec_id,
            "is_valid": is_valid,
            "validation_results": validation_results
        }

    def _update_plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing plan"""
        spec_id = input_data.get("spec_id")
        if not spec_id:
            return {"error": "spec_id is required for plan update"}

        plan = self.plan_builder.get_plan(spec_id)
        if not plan:
            return {"error": f"Plan for spec '{spec_id}' not found"}

        # Update phases if provided
        if "phase_updates" in input_data:
            for update in input_data["phase_updates"]:
                phase_name = update.get("phase_name")
                new_status = update.get("status")
                if phase_name and new_status:
                    plan.update_phase_status(phase_name, new_status)

        return {
            "success": True,
            "spec_id": spec_id,
            "updated_phases": len(input_data.get("phase_updates", []))
        }

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