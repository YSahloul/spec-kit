"""
Specification entity model
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Specification:
    """Represents a feature specification"""

    id: str
    description: str
    branch: str
    path: str
    status: str = "draft"
    template: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Set default values"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    @property
    def is_draft(self) -> bool:
        """Check if specification is in draft status"""
        return self.status == "draft"

    @property
    def is_approved(self) -> bool:
        """Check if specification is approved"""
        return self.status == "approved"

    @property
    def is_in_progress(self) -> bool:
        """Check if specification is in progress"""
        return self.status == "in_progress"

    @property
    def is_completed(self) -> bool:
        """Check if specification is completed"""
        return self.status == "completed"

    def update_status(self, new_status: str) -> None:
        """Update specification status"""
        valid_statuses = ["draft", "approved", "in_progress", "completed"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")
        self.status = new_status
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "description": self.description,
            "branch": self.branch,
            "path": self.path,
            "status": self.status,
            "template": self.template,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Specification':
        """Create from dictionary representation"""
        return cls(
            id=data["id"],
            description=data["description"],
            branch=data["branch"],
            path=data["path"],
            status=data.get("status", "draft"),
            template=data.get("template"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )