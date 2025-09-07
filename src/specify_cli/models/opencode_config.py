"""
OpenCodeConfig entity model
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class OpenCodeConfig:
    """Represents OpenCode-specific configuration for spec-kit"""

    version: str = "1.0.0"
    theme: str = "auto"
    auto_save: bool = True
    keyboard_shortcuts: Optional[Dict[str, str]] = None
    extensions: Optional[Dict[str, bool]] = None
    workspace_settings: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Set default values"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.keyboard_shortcuts is None:
            self.keyboard_shortcuts = {}
        if self.extensions is None:
            self.extensions = {}
        if self.workspace_settings is None:
            self.workspace_settings = {}

    def update_shortcut(self, command: str, shortcut: str) -> None:
        """Update a keyboard shortcut"""
        if self.keyboard_shortcuts is None:
            self.keyboard_shortcuts = {}
        self.keyboard_shortcuts[command] = shortcut
        self.updated_at = datetime.now()

    def enable_extension(self, extension: str) -> None:
        """Enable an extension"""
        if self.extensions is None:
            self.extensions = {}
        self.extensions[extension] = True
        self.updated_at = datetime.now()

    def disable_extension(self, extension: str) -> None:
        """Disable an extension"""
        if self.extensions is None:
            self.extensions = {}
        self.extensions[extension] = False
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "version": self.version,
            "theme": self.theme,
            "auto_save": self.auto_save,
            "keyboard_shortcuts": self.keyboard_shortcuts or {},
            "extensions": self.extensions or {},
            "workspace_settings": self.workspace_settings or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'OpenCodeConfig':
        """Create from dictionary representation"""
        return cls(
            version=data.get("version", "1.0.0"),
            theme=data.get("theme", "auto"),
            auto_save=data.get("auto_save", True),
            keyboard_shortcuts=data.get("keyboard_shortcuts", {}),
            extensions=data.get("extensions", {}),
            workspace_settings=data.get("workspace_settings", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )