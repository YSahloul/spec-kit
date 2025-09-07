"""
Spec-builder agent implementation
"""

from typing import Dict, Any, Optional
from datetime import datetime

from specify_cli.services.spec_generator import SpecGenerator
from specify_cli.models.specification import Specification


class SpecBuilderAgent:
    """Agent for building specifications - OpenCode compatible"""

    def __init__(self):
        self.generator = SpecGenerator()
        self.name = "spec-builder"
        self.description = "Creates and manages feature specifications"
        self.version = "1.0.0"
        self.author = "spec-kit"
        self.capabilities = ["create_spec", "validate_spec", "update_spec"]
        self.supported_actions = ["create", "validate", "update"]
        self.metadata = {
            "category": "specification",
            "tags": ["spec", "creation", "validation"],
            "requires_project": True,
            "input_schema": {
                "create": {
                    "description": {"type": "string", "required": True},
                    "template": {"type": "string", "required": False},
                    "branch": {"type": "string", "required": False}
                },
                "validate": {
                    "spec_id": {"type": "string", "required": True}
                },
                "update": {
                    "spec_id": {"type": "string", "required": True},
                    "description": {"type": "string", "required": False},
                    "status": {"type": "string", "required": False}
                }
            }
        }

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute spec building task"""
        action = input_data.get("action", "create")

        if action == "create":
            return self._create_specification(input_data)
        elif action == "validate":
            return self._validate_specification(input_data)
        elif action == "update":
            return self._update_specification(input_data)
        else:
            return {
                "error": f"Unknown action: {action}",
                "supported_actions": self.capabilities
            }

    def _create_specification(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new specification"""
        description = input_data.get("description")
        if not description:
            return {"error": "Description is required for spec creation"}

        template = input_data.get("template")
        branch = input_data.get("branch")

        try:
            spec = self.generator.create_spec(
                description=description,
                template_name=template,
                branch_name=branch
            )

            return {
                "success": True,
                "spec_id": spec.id,
                "branch": spec.branch,
                "path": spec.path,
                "status": spec.status
            }
        except Exception as e:
            return {"error": f"Failed to create specification: {str(e)}"}

    def _validate_specification(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an existing specification"""
        spec_id = input_data.get("spec_id")
        if not spec_id:
            return {"error": "spec_id is required for validation"}

        spec = self.generator.get_spec(spec_id)
        if not spec:
            return {"error": f"Specification '{spec_id}' not found"}

        # Basic validation
        validation_results = {
            "has_description": bool(spec.description),
            "has_valid_status": spec.status in ["draft", "approved", "in_progress", "completed"],
            "has_path": bool(spec.path)
        }

        is_valid = all(validation_results.values())

        return {
            "spec_id": spec_id,
            "is_valid": is_valid,
            "validation_results": validation_results
        }

    def _update_specification(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing specification"""
        spec_id = input_data.get("spec_id")
        if not spec_id:
            return {"error": "spec_id is required for update"}

        spec = self.generator.get_spec(spec_id)
        if not spec:
            return {"error": f"Specification '{spec_id}' not found"}

        # Update fields if provided
        if "description" in input_data:
            spec.description = input_data["description"]
        if "status" in input_data:
            spec.update_status(input_data["status"])

        return {
            "success": True,
            "spec_id": spec_id,
            "updated_fields": list(input_data.keys())
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

    def get_metadata(self) -> Dict[str, Any]:
        """Get agent metadata for OpenCode integration"""
        return self.metadata.copy()

    def validate_input(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data for an action"""
        if action not in self.supported_actions:
            return {
                'valid': False,
                'error': f'Unsupported action: {action}',
                'supported_actions': self.supported_actions
            }

        schema = self.metadata['input_schema'].get(action, {})
        validation_errors = []

        for field, requirements in schema.items():
            if requirements.get('required', False) and field not in input_data:
                validation_errors.append(f'Missing required field: {field}')
            elif field in input_data:
                field_type = requirements.get('type')
                if field_type == 'string' and not isinstance(input_data[field], str):
                    validation_errors.append(f'Field {field} must be a string')

        return {
            'valid': len(validation_errors) == 0,
            'errors': validation_errors if validation_errors else None
        }

    def get_help(self, action: str = None) -> str:
        """Get help information for the agent"""
        if action:
            if action in self.metadata['input_schema']:
                schema = self.metadata['input_schema'][action]
                help_text = f"Action: {action}\n"
                help_text += "Required fields:\n"
                for field, req in schema.items():
                    if req.get('required'):
                        field_type = req.get('type', 'any')
                        help_text += f"  - {field}: {field_type}\n"
                help_text += "Optional fields:\n"
                for field, req in schema.items():
                    if not req.get('required'):
                        field_type = req.get('type', 'any')
                        help_text += f"  - {field}: {field_type}\n"
                return help_text
            else:
                return f"Unknown action: {action}"
        else:
            return f"""
{self.name} Agent v{self.version}
{self.description}

Supported actions: {', '.join(self.supported_actions)}
Capabilities: {', '.join(self.capabilities)}

Use get_help('action_name') for details on specific actions.
"""

    def is_healthy(self) -> bool:
        """Check if the agent is healthy and ready"""
        try:
            # Check if dependencies are available
            return hasattr(self, 'generator') and self.generator is not None
        except Exception:
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return {
            'name': self.name,
            'version': self.version,
            'uptime': 'unknown',  # Could track actual uptime
            'requests_processed': 0,  # Could track actual usage
            'error_rate': 0.0,
            'last_activity': datetime.now().isoformat()
        }