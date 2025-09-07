"""
ResearchItem entity model
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class ResearchItem:
    """Represents a research item or finding"""

    topic: str
    content: str
    source: str = "web"
    spec_id: Optional[str] = None
    findings: Optional[str] = None
    decision: Optional[str] = None
    alternatives: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Set default values"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.alternatives is None:
            self.alternatives = []
        if self.tags is None:
            self.tags = []

    def add_alternative(self, alternative: str) -> None:
        """Add an alternative approach"""
        if self.alternatives is None:
            self.alternatives = []
        self.alternatives.append(alternative)
        self.updated_at = datetime.now()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the research item"""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()

    def set_decision(self, decision: str) -> None:
        """Set the decision for this research item"""
        self.decision = decision
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "topic": self.topic,
            "content": self.content,
            "source": self.source,
            "spec_id": self.spec_id,
            "findings": self.findings,
            "decision": self.decision,
            "alternatives": self.alternatives or [],
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ResearchItem':
        """Create from dictionary representation"""
        return cls(
            topic=data["topic"],
            content=data["content"],
            source=data.get("source", "web"),
            spec_id=data.get("spec_id"),
            findings=data.get("findings"),
            decision=data.get("decision"),
            alternatives=data.get("alternatives", []),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )