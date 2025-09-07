"""
CommandRegistry - Manages OpenCode command registration and discovery
"""

import json
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass, asdict
from datetime import datetime

from specify_cli.services.configuration_service import ConfigurationService


@dataclass
class CommandMetadata:
    """Metadata for a registered command"""
    name: str
    description: str
    category: str
    aliases: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    examples: Optional[List[str]] = None
    version: str = "1.0.0"
    author: str = "spec-kit"
    tags: Optional[List[str]] = None
    requires_project: bool = False
    hidden: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Set default values"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.aliases is None:
            self.aliases = []
        if self.parameters is None:
            self.parameters = {}
        if self.examples is None:
            self.examples = []
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "aliases": self.aliases or [],
            "parameters": self.parameters or {},
            "examples": self.examples or [],
            "version": self.version,
            "author": self.author,
            "tags": self.tags or [],
            "requires_project": self.requires_project,
            "hidden": self.hidden,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandMetadata':
        """Create from dictionary representation"""
        return cls(
            name=data["name"],
            description=data["description"],
            category=data["category"],
            aliases=data.get("aliases", []),
            parameters=data.get("parameters", {}),
            examples=data.get("examples", []),
            version=data.get("version", "1.0.0"),
            author=data.get("author", "spec-kit"),
            tags=data.get("tags", []),
            requires_project=data.get("requires_project", False),
            hidden=data.get("hidden", False),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


@dataclass
class RegisteredCommand:
    """A registered command with its handler"""
    metadata: CommandMetadata
    handler: Callable
    module_path: str
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "metadata": self.metadata.to_dict(),
            "module_path": self.module_path,
            "enabled": self.enabled,
        }


class CommandRegistry:
    """Registry for managing OpenCode commands"""

    def __init__(self, config_service: Optional[ConfigurationService] = None):
        self.config_service = config_service or ConfigurationService()
        self.commands: Dict[str, RegisteredCommand] = {}
        self.categories: Dict[str, List[str]] = {}
        self._loaded = False

    def register_command(
        self,
        name: str,
        handler: Callable,
        description: str,
        category: str = "general",
        aliases: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        examples: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        requires_project: bool = False,
        hidden: bool = False,
        version: str = "1.0.0"
    ) -> None:
        """Register a new command"""
        # Create metadata
        metadata = CommandMetadata(
            name=name,
            description=description,
            category=category,
            aliases=aliases or [],
            parameters=parameters or {},
            examples=examples or [],
            tags=tags or [],
            requires_project=requires_project,
            hidden=hidden,
            version=version,
        )

        # Get module path
        module_path = getattr(handler, '__module__', 'unknown')

        # Create registered command
        registered_command = RegisteredCommand(
            metadata=metadata,
            handler=handler,
            module_path=module_path,
            enabled=True
        )

        # Register command
        self.commands[name] = registered_command

        # Add to category
        if category not in self.categories:
            self.categories[category] = []
        if name not in self.categories[category]:
            self.categories[category].append(name)

        # Register aliases
        if metadata.aliases:
            for alias in metadata.aliases:
                if alias not in self.commands:
                    self.commands[alias] = registered_command

    def unregister_command(self, name: str) -> bool:
        """Unregister a command"""
        if name not in self.commands:
            return False

        command = self.commands[name]

        # Remove from category
        if command.metadata.category in self.categories:
            if name in self.categories[command.metadata.category]:
                self.categories[command.metadata.category].remove(name)

        # Remove command and aliases
        aliases_to_remove = [name]
        if command.metadata.aliases:
            aliases_to_remove.extend(command.metadata.aliases)
        for alias in aliases_to_remove:
            if alias in self.commands:
                del self.commands[alias]

        return True

    def get_command(self, name: str) -> Optional[RegisteredCommand]:
        """Get a registered command by name or alias"""
        return self.commands.get(name)

    def list_commands(
        self,
        category: Optional[str] = None,
        include_hidden: bool = False,
        include_disabled: bool = False
    ) -> List[RegisteredCommand]:
        """List registered commands"""
        commands = []

        for name, command in self.commands.items():
            # Skip if it's an alias (not the primary command)
            if command.metadata.name != name:
                continue

            # Filter by category
            if category and command.metadata.category != category:
                continue

            # Filter hidden commands
            if command.metadata.hidden and not include_hidden:
                continue

            # Filter disabled commands
            if not command.enabled and not include_disabled:
                continue

            commands.append(command)

        return commands

    def list_categories(self) -> List[str]:
        """List all command categories"""
        return list(self.categories.keys())

    def search_commands(
        self,
        query: str,
        category: Optional[str] = None,
        include_hidden: bool = False
    ) -> List[RegisteredCommand]:
        """Search commands by name, description, or tags"""
        query_lower = query.lower()
        results = []

        for command in self.list_commands(category=category if category else None, include_hidden=include_hidden):
            # Search in name
            if query_lower in command.metadata.name.lower():
                results.append(command)
                continue

            # Search in description
            if query_lower in command.metadata.description.lower():
                results.append(command)
                continue

            # Search in tags
            if command.metadata.tags:
                for tag in command.metadata.tags:
                    if query_lower in tag.lower():
                        results.append(command)
                        break

        return results

    def execute_command(
        self,
        name: str,
        args: Optional[List[str]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a registered command"""
        command = self.get_command(name)
        if not command:
            raise ValueError(f"Command '{name}' not found")

        if not command.enabled:
            raise ValueError(f"Command '{name}' is disabled")

        # Prepare arguments
        args = args or []
        kwargs = kwargs or {}
        context = context or {}

        # Check if project is required
        if command.metadata.requires_project:
            project_path = context.get('project_path')
            if not project_path:
                raise ValueError(f"Command '{name}' requires a project context")

        # Execute command
        try:
            return command.handler(*args, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Command '{name}' execution failed: {str(e)}")

    def get_command_help(self, name: str) -> Optional[Dict[str, Any]]:
        """Get help information for a command"""
        command = self.get_command(name)
        if not command:
            return None

        return {
            "name": command.metadata.name,
            "description": command.metadata.description,
            "category": command.metadata.category,
            "aliases": command.metadata.aliases or [],
            "parameters": command.metadata.parameters or {},
            "examples": command.metadata.examples or [],
            "version": command.metadata.version,
            "author": command.metadata.author,
            "tags": command.metadata.tags or [],
            "requires_project": command.metadata.requires_project,
            "enabled": command.enabled,
        }

    def get_command_signature(self, name: str) -> Optional[str]:
        """Get the function signature for a command"""
        command = self.get_command(name)
        if not command:
            return None

        try:
            sig = inspect.signature(command.handler)
            return f"{name}{sig}"
        except (ValueError, TypeError):
            return f"{name}(...)"

    def enable_command(self, name: str) -> bool:
        """Enable a command"""
        command = self.get_command(name)
        if command:
            command.enabled = True
            return True
        return False

    def disable_command(self, name: str) -> bool:
        """Disable a command"""
        command = self.get_command(name)
        if command:
            command.enabled = False
            return True
        return False

    def is_command_enabled(self, name: str) -> bool:
        """Check if a command is enabled"""
        command = self.get_command(name)
        return command is not None and command.enabled

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total_commands = len([c for c in self.commands.values() if c.metadata.name == list(self.commands.keys())[list(self.commands.values()).index(c)]])
        enabled_commands = len([c for c in self.commands.values() if c.enabled and c.metadata.name == list(self.commands.keys())[list(self.commands.values()).index(c)]])
        categories = len(self.categories)

        return {
            "total_commands": total_commands,
            "enabled_commands": enabled_commands,
            "disabled_commands": total_commands - enabled_commands,
            "categories": categories,
            "commands_per_category": {cat: len(cmds) for cat, cmds in self.categories.items()},
        }

    def to_dict(self) -> Dict[str, Any]:
        """Export registry to dictionary"""
        return {
            "commands": {
                name: cmd.to_dict() for name, cmd in self.commands.items()
                if cmd.metadata.name == name  # Only include primary commands, not aliases
            },
            "categories": self.categories.copy(),
            "stats": self.get_stats(),
        }

    def clear(self) -> None:
        """Clear all registered commands"""
        self.commands.clear()
        self.categories.clear()