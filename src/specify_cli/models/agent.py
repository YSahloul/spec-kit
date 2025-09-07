"""
Agent entity model
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Agent:
    """Represents an agent in the spec-kit system"""

    name: str
    type: str
    description: str
    capabilities: Optional[List[str]] = None
    configuration: Optional[Dict[str, Any]] = None
    is_active: bool = True
    version: str = "1.0.0"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_used: Optional[datetime] = None

    def __post_init__(self):
        """Set default values"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.capabilities is None:
            self.capabilities = []
        if self.configuration is None:
            self.configuration = {}

    def add_capability(self, capability: str) -> None:
        """Add a capability to the agent"""
        if self.capabilities is None:
            self.capabilities = []
        if capability not in self.capabilities:
            self.capabilities.append(capability)
            self.updated_at = datetime.now()

    def remove_capability(self, capability: str) -> None:
        """Remove a capability from the agent"""
        if self.capabilities and capability in self.capabilities:
            self.capabilities.remove(capability)
            self.updated_at = datetime.now()

    def update_configuration(self, key: str, value: Any) -> None:
        """Update agent configuration"""
        if self.configuration is None:
            self.configuration = {}
        self.configuration[key] = value
        self.updated_at = datetime.now()

    def get_configuration(self, key: str, default: Any = None) -> Any:
        """Get agent configuration value"""
        if self.configuration is None:
            return default
        return self.configuration.get(key, default)

    def mark_used(self) -> None:
        """Mark the agent as recently used"""
        self.last_used = datetime.now()
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Activate the agent"""
        self.is_active = True
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """Deactivate the agent"""
        self.is_active = False
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "capabilities": self.capabilities or [],
            "configuration": self.configuration or {},
            "is_active": self.is_active,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Agent':
        """Create from dictionary representation"""
        return cls(
            name=data["name"],
            type=data["type"],
            description=data["description"],
            capabilities=data.get("capabilities", []),
            configuration=data.get("configuration", {}),
            is_active=data.get("is_active", True),
            version=data.get("version", "1.0.0"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
        )