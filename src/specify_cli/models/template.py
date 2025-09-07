"""
Template entity model
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Template:
    """Represents a template for specifications"""

    name: str
    description: str
    category: str = "general"
    content: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_builtin: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Set default values"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.variables is None:
            self.variables = {}
        if self.tags is None:
            self.tags = []

    def add_tag(self, tag: str) -> None:
        """Add a tag to the template"""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the template"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()

    def set_variable(self, key: str, value: Any) -> None:
        """Set a template variable"""
        if self.variables is None:
            self.variables = {}
        self.variables[key] = value
        self.updated_at = datetime.now()

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a template variable"""
        if self.variables is None:
            return default
        return self.variables.get(key, default)

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "content": self.content,
            "variables": self.variables or {},
            "tags": self.tags or [],
            "is_builtin": self.is_builtin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Template':
        """Create from dictionary representation"""
        return cls(
            name=data["name"],
            description=data["description"],
            category=data.get("category", "general"),
            content=data.get("content"),
            variables=data.get("variables", {}),
            tags=data.get("tags", []),
            is_builtin=data.get("is_builtin", False),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )