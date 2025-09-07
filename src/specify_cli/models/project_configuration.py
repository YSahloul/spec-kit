"""
ProjectConfiguration entity model
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class ProjectConfiguration:
    """Represents project-level configuration for spec-kit"""

    project_path: str
    spec_kit_enabled: bool = True
    default_template: Optional[str] = None
    auto_commit: bool = True
    git_integration: bool = True
    research_enabled: bool = True
    custom_settings: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Set default values"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.custom_settings is None:
            self.custom_settings = {}

    def update_setting(self, key: str, value: Any) -> None:
        """Update a custom setting"""
        if self.custom_settings is None:
            self.custom_settings = {}
        self.custom_settings[key] = value
        self.updated_at = datetime.now()

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a custom setting"""
        if self.custom_settings is None:
            return default
        return self.custom_settings.get(key, default)

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "project_path": self.project_path,
            "spec_kit_enabled": self.spec_kit_enabled,
            "default_template": self.default_template,
            "auto_commit": self.auto_commit,
            "git_integration": self.git_integration,
            "research_enabled": self.research_enabled,
            "custom_settings": self.custom_settings or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ProjectConfiguration':
        """Create from dictionary representation"""
        return cls(
            project_path=data["project_path"],
            spec_kit_enabled=data.get("spec_kit_enabled", True),
            default_template=data.get("default_template"),
            auto_commit=data.get("auto_commit", True),
            git_integration=data.get("git_integration", True),
            research_enabled=data.get("research_enabled", True),
            custom_settings=data.get("custom_settings", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )