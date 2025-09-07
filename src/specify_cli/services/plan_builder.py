"""
PlanBuilder service
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from specify_cli.models.specification import Specification
from specify_cli.models.implementation_plan import ImplementationPlan


class PlanBuilder:
    """Service for building implementation plans"""

    def __init__(self, base_path: str = "."):
        self.base_path = base_path

    def create_plan(
        self,
        spec: Specification,
        technical_context: Optional[Dict[str, Any]] = None
    ) -> ImplementationPlan:
        """Create an implementation plan for a specification"""
        # Generate plan path
        plan_path = f"specs/{spec.id}/plan.md"

        # Create plan object
        plan = ImplementationPlan(
            spec_id=spec.id,
            path=plan_path,
            technical_context=technical_context
        )

        # Generate phases based on specification
        self._generate_phases(plan, spec)

        # Create plan file
        self._create_plan_file(plan, spec)

        return plan

    def _generate_phases(self, plan: ImplementationPlan, spec: Specification) -> None:
        """Generate implementation phases"""
        # Default phases for any specification
        default_phases = [
            {
                "name": "setup",
                "status": "pending",
                "artifacts": ["project-structure", "dependencies"]
            },
            {
                "name": "implementation",
                "status": "pending",
                "artifacts": ["core-features", "business-logic"]
            },
            {
                "name": "testing",
                "status": "pending",
                "artifacts": ["unit-tests", "integration-tests"]
            },
            {
                "name": "deployment",
                "status": "pending",
                "artifacts": ["deployment-config", "documentation"]
            }
        ]

        for phase_data in default_phases:
            plan.add_phase(**phase_data)

    def _create_plan_file(self, plan: ImplementationPlan, spec: Specification) -> None:
        """Create the plan markdown file"""
        import os
        from pathlib import Path

        plan_file = Path(self.base_path) / "specs" / spec.id / "plan.md"
        plan_file.parent.mkdir(parents=True, exist_ok=True)

        content = self._generate_plan_content(plan, spec)

        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_plan_content(self, plan: ImplementationPlan, spec: Specification) -> str:
        """Generate plan file content"""
        content = f"""# Implementation Plan: {spec.id}

## Specification
**Description**: {spec.description}
**Branch**: {spec.branch}
**Created**: {spec.created_at.strftime('%Y-%m-%d %H:%M:%S') if spec.created_at else 'TBD'}

## Technical Context
"""

        if plan.technical_context:
            for key, value in plan.technical_context.items():
                content += f"- **{key}**: {value}\n"
        else:
            content += "- TBD\n"

        content += "\n## Implementation Phases\n\n"

        for phase in plan.phases:
            content += f"### {phase['name'].title()}\n"
            content += f"**Status**: {phase['status']}\n"
            content += "**Artifacts**:\n"
            for artifact in phase['artifacts']:
                content += f"- {artifact}\n"
            content += "\n"

        content += "## Tasks\n\n"
        content += "- [ ] Task 1\n"
        content += "- [ ] Task 2\n"
        content += "- [ ] Task 3\n\n"

        content += "## Notes\n\n"
        content += "Implementation notes and decisions will be documented here.\n"

        return content

    def get_plan(self, spec_id: str) -> Optional[ImplementationPlan]:
        """Get a plan by specification ID"""
        import os
        from pathlib import Path

        plan_file = Path(self.base_path) / "specs" / spec_id / "plan.md"
        if not plan_file.exists():
            return None

        # Read plan file and extract metadata
        return ImplementationPlan(
            spec_id=spec_id,
            path=f"specs/{spec_id}/plan.md"
        )

    def update_phase_status(self, spec_id: str, phase_name: str, status: str) -> bool:
        """Update the status of a plan phase"""
        plan = self.get_plan(spec_id)
        if not plan:
            return False

        plan.update_phase_status(phase_name, status)
        # In a real implementation, this would save the updated plan
        return True