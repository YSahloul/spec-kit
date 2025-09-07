"""
SpecGenerator service
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from specify_cli.models.specification import Specification
from specify_cli.models.template import Template
from specify_cli.services.configuration_service import ConfigurationService


class SpecGenerator:
    """Service for generating specifications"""

    def __init__(self, base_path: str = ".", config_service: Optional[ConfigurationService] = None):
        self.base_path = Path(base_path)
        self.specs_dir = self.base_path / "specs"
        self.config_service = config_service or ConfigurationService()

        # Load project configuration
        self.project_config = self.config_service.load_project_config(self.base_path)

    def create_spec(
        self,
        description: str,
        template_name: Optional[str] = None,
        branch_name: Optional[str] = None
    ) -> Specification:
        """Create a new specification"""
        # Use configuration for default template if none provided
        if template_name is None:
            template_name = self.config_service.get_default_template(self.base_path)

        # Generate spec ID from description
        spec_id = self._generate_spec_id(description)

        # Use provided branch name or default to spec ID
        branch = branch_name or spec_id

        # Create spec path
        spec_path = f"specs/{spec_id}/spec.md"

        # Create specification object
        spec = Specification(
            id=spec_id,
            description=description,
            branch=branch,
            path=spec_path,
            template=template_name
        )

        # Create the spec directory and file
        self._create_spec_directory(spec)
        self._create_spec_file(spec, template_name)

        return spec

    def _generate_spec_id(self, description: str) -> str:
        """Generate a specification ID from description"""
        # Clean and format the description
        clean_desc = description.lower().replace(" ", "-")
        # Remove special characters
        clean_desc = "".join(c for c in clean_desc if c.isalnum() or c in "-_")
        # Take first 50 characters and add timestamp
        prefix = clean_desc[:50].rstrip("-_")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"{prefix}-{timestamp}"

    def _create_spec_directory(self, spec: Specification) -> None:
        """Create the specification directory"""
        spec_dir = self.base_path / "specs" / spec.id
        spec_dir.mkdir(parents=True, exist_ok=True)

    def _create_spec_file(self, spec: Specification, template_name: Optional[str] = None) -> None:
        """Create the specification markdown file"""
        spec_file = self.base_path / "specs" / spec.id / "spec.md"

        # Get template content or use default
        content = self._get_template_content(template_name)

        # Replace template variables
        content = self._populate_template(content, spec)

        # Write the file
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def _get_template_content(self, template_name: Optional[str] = None) -> str:
        """Get template content"""
        if template_name:
            # Try to load template from templates directory
            template_path = self.base_path / "templates" / f"{template_name}.md"
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()

        # Return default template
        return self._get_default_template()

    def _get_default_template(self) -> str:
        """Get the default specification template"""
        return f"""# Specification: {{description}}

## Overview
{{description}}

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2
- [ ] Criteria 3

## Technical Notes
- **ID**: {{id}}
- **Branch**: {{branch}}
- **Created**: {{created_at}}

## Implementation Plan
TBD

## Testing Strategy
TBD
"""

    def _populate_template(self, template: str, spec: Specification) -> str:
        """Populate template with specification data"""
        replacements = {
            "{{description}}": spec.description,
            "{{id}}": spec.id,
            "{{branch}}": spec.branch,
            "{{created_at}}": spec.created_at.strftime("%Y-%m-%d %H:%M:%S") if spec.created_at else "TBD",
            "{{template}}": spec.template or "default"
        }

        for placeholder, value in replacements.items():
            template = template.replace(placeholder, str(value))

        return template

    def get_spec(self, spec_id: str) -> Optional[Specification]:
        """Get a specification by ID"""
        spec_file = self.base_path / "specs" / spec_id / "spec.md"
        if not spec_file.exists():
            return None

        # Read spec file and extract metadata
        # This is a simplified implementation
        return Specification(
            id=spec_id,
            description=f"Specification {spec_id}",
            branch=spec_id,
            path=f"specs/{spec_id}/spec.md"
        )

    def list_specs(self) -> list[Specification]:
        """List all specifications"""
        specs = []
        specs_dir = self.base_path / "specs"

        if specs_dir.exists():
            for spec_dir in specs_dir.iterdir():
                if spec_dir.is_dir():
                    spec = self.get_spec(spec_dir.name)
                    if spec:
                        specs.append(spec)

        return specs