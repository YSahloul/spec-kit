"""
MigrationState entity model
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class MigrationState:
    """Represents the state of a migration process"""

    id: str
    mode: str = "incremental"
    status: str = "initiated"
    preserve_structure: bool = True
    specs_created: Optional[List[str]] = None
    next_steps: Optional[List[str]] = None
    progress: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Set default values"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.specs_created is None:
            self.specs_created = []
        if self.next_steps is None:
            self.next_steps = []
        if self.progress is None:
            self.progress = {}
        if self.errors is None:
            self.errors = []

    @property
    def is_initiated(self) -> bool:
        """Check if migration is initiated"""
        return self.status == "initiated"

    @property
    def is_in_progress(self) -> bool:
        """Check if migration is in progress"""
        return self.status == "in_progress"

    @property
    def is_completed(self) -> bool:
        """Check if migration is completed"""
        return self.status == "completed"

    def update_status(self, new_status: str) -> None:
        """Update migration status"""
        valid_statuses = ["initiated", "in_progress", "completed", "failed"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")

        self.status = new_status
        self.updated_at = datetime.now()

        if new_status == "completed" and self.completed_at is None:
            self.completed_at = datetime.now()

    def add_spec_created(self, spec_id: str) -> None:
        """Add a created spec to the list"""
        if self.specs_created is None:
            self.specs_created = []
        self.specs_created.append(spec_id)
        self.updated_at = datetime.now()

    def add_error(self, error: str) -> None:
        """Add an error to the list"""
        if self.errors is None:
            self.errors = []
        self.errors.append(error)
        self.updated_at = datetime.now()

    def update_progress(self, key: str, value: Any) -> None:
        """Update progress information"""
        if self.progress is None:
            self.progress = {}
        self.progress[key] = value
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "mode": self.mode,
            "status": self.status,
            "preserve_structure": self.preserve_structure,
            "specs_created": self.specs_created or [],
            "next_steps": self.next_steps or [],
            "progress": self.progress or {},
            "errors": self.errors or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MigrationState':
        """Create from dictionary representation"""
        return cls(
            id=data["id"],
            mode=data.get("mode", "incremental"),
            status=data.get("status", "initiated"),
            preserve_structure=data.get("preserve_structure", True),
            specs_created=data.get("specs_created", []),
            next_steps=data.get("next_steps", []),
            progress=data.get("progress", {}),
            errors=data.get("errors", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )