"""
ImplementationPlan entity model
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class ImplementationPlan:
    """Represents an implementation plan for a specification"""

    spec_id: str
    path: str
    phases: List[Dict[str, Any]]
    technical_context: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Set default values"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.phases is None:
            self.phases = []

    def add_phase(self, name: str, status: str = "pending", artifacts: Optional[List[str]] = None) -> None:
        """Add a phase to the plan"""
        if artifacts is None:
            artifacts = []

        phase = {
            "name": name,
            "status": status,
            "artifacts": artifacts
        }
        self.phases.append(phase)
        self.updated_at = datetime.now()

    def update_phase_status(self, phase_name: str, status: str) -> None:
        """Update the status of a phase"""
        for phase in self.phases:
            if phase["name"] == phase_name:
                phase["status"] = status
                self.updated_at = datetime.now()
                break

    def get_pending_phases(self) -> List[Dict[str, Any]]:
        """Get all pending phases"""
        return [phase for phase in self.phases if phase["status"] == "pending"]

    def get_completed_phases(self) -> List[Dict[str, Any]]:
        """Get all completed phases"""
        return [phase for phase in self.phases if phase["status"] == "completed"]

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "spec_id": self.spec_id,
            "path": self.path,
            "phases": self.phases,
            "technical_context": self.technical_context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ImplementationPlan':
        """Create from dictionary representation"""
        return cls(
            spec_id=data["spec_id"],
            path=data["path"],
            phases=data.get("phases", []),
            technical_context=data.get("technical_context"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )