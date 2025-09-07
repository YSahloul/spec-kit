"""
Task entity model
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class Task:
    """Represents a task in the implementation plan"""

    id: str
    content: str
    status: str = "pending"
    priority: str = "medium"
    plan_id: Optional[str] = None
    dependencies: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Set default values"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.dependencies is None:
            self.dependencies = []

    @property
    def is_pending(self) -> bool:
        """Check if task is pending"""
        return self.status == "pending"

    @property
    def is_in_progress(self) -> bool:
        """Check if task is in progress"""
        return self.status == "in_progress"

    @property
    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.status == "completed"

    @property
    def is_cancelled(self) -> bool:
        """Check if task is cancelled"""
        return self.status == "cancelled"

    def update_status(self, new_status: str) -> None:
        """Update task status"""
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")

        self.status = new_status
        self.updated_at = datetime.now()

        if new_status == "completed" and self.completed_at is None:
            self.completed_at = datetime.now()

    def add_dependency(self, task_id: str) -> None:
        """Add a dependency to this task"""
        if self.dependencies is None:
            self.dependencies = []
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
            self.updated_at = datetime.now()

    def remove_dependency(self, task_id: str) -> None:
        """Remove a dependency from this task"""
        if self.dependencies and task_id in self.dependencies:
            self.dependencies.remove(task_id)
            self.updated_at = datetime.now()

    def can_start(self) -> bool:
        """Check if task can be started (all dependencies completed)"""
        # This would need to check against other tasks in the system
        # For now, return True if no dependencies
        return not self.dependencies or len(self.dependencies) == 0

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "content": self.content,
            "status": self.status,
            "priority": self.priority,
            "plan_id": self.plan_id,
            "dependencies": self.dependencies or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """Create from dictionary representation"""
        return cls(
            id=data["id"],
            content=data["content"],
            status=data.get("status", "pending"),
            priority=data.get("priority", "medium"),
            plan_id=data.get("plan_id"),
            dependencies=data.get("dependencies", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )