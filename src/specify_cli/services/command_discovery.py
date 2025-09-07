"""
CommandDiscovery - Automatically discovers and registers OpenCode commands
"""

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

from specify_cli.services.command_registry import CommandRegistry, CommandMetadata


@dataclass
class DiscoveredCommand:
    """A command discovered from a module"""
    name: str
    handler: Callable
    module_name: str
    metadata: Optional[CommandMetadata] = None


class CommandDiscovery:
    """Service for automatically discovering and registering commands"""

    def __init__(self, registry: CommandRegistry):
        self.registry = registry
        self.discovered_commands: Dict[str, DiscoveredCommand] = {}

    def discover_commands(self, base_module: str = "specify_cli.opencode.commands") -> List[DiscoveredCommand]:
        """Discover all commands in the specified module"""
        discovered = []

        try:
            # Import the base module
            module = importlib.import_module(base_module)

            # Get the module path
            if hasattr(module, '__path__'):
                # It's a package
                for _, name, _ in pkgutil.iter_modules(module.__path__, base_module + "."):
                    try:
                        sub_module = importlib.import_module(name)
                        commands = self._discover_commands_in_module(sub_module, name)
                        discovered.extend(commands)
                    except ImportError as e:
                        print(f"Warning: Could not import {name}: {e}")
            else:
                # It's a single module
                commands = self._discover_commands_in_module(module, base_module)
                discovered.extend(commands)

        except ImportError as e:
            print(f"Warning: Could not import base module {base_module}: {e}")

        self.discovered_commands = {cmd.name: cmd for cmd in discovered}
        return discovered

    def _discover_commands_in_module(self, module, module_name: str) -> List[DiscoveredCommand]:
        """Discover commands in a specific module"""
        commands = []

        # Look for functions that start with 'cmd_' or have command metadata
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) or inspect.ismethod(obj):
                # Check if it's a command function
                if self._is_command_function(name, obj):
                    command = self._create_command_from_function(name, obj, module_name)
                    if command:
                        commands.append(command)

        return commands

    def _is_command_function(self, name: str, func: Callable) -> bool:
        """Check if a function is a command"""
        # Check function name patterns
        if name.startswith('cmd_') or name.startswith('command_'):
            return True

        # Check for command metadata in docstring or attributes
        if hasattr(func, '__doc__') and func.__doc__:
            docstring = func.__doc__.lower()
            if any(keyword in docstring for keyword in ['command', 'cmd', '@command']):
                return True

        # Check for command attributes
        if hasattr(func, '_is_command') and getattr(func, '_is_command'):
            return True

        return False

    def _create_command_from_function(self, name: str, func: Callable, module_name: str) -> Optional[DiscoveredCommand]:
        """Create a DiscoveredCommand from a function"""
        try:
            # Extract command name
            cmd_name = self._extract_command_name(name, func)

            # Extract metadata
            metadata = self._extract_command_metadata(name, func, module_name)

            return DiscoveredCommand(
                name=cmd_name,
                handler=func,
                module_name=module_name,
                metadata=metadata
            )
        except Exception as e:
            print(f"Warning: Could not create command from {name}: {e}")
            return None

    def _extract_command_name(self, func_name: str, func: Callable) -> str:
        """Extract the command name from function name or attributes"""
        # Check for explicit name attribute
        if hasattr(func, '_command_name'):
            return getattr(func, '_command_name')

        # Remove common prefixes
        name = func_name
        if name.startswith('cmd_'):
            name = name[4:]
        elif name.startswith('command_'):
            name = name[8:]

        # Convert snake_case to kebab-case
        return name.replace('_', '-')

    def _extract_command_metadata(self, func_name: str, func: Callable, module_name: str) -> CommandMetadata:
        """Extract command metadata from function"""
        # Default metadata
        metadata = CommandMetadata(
            name=self._extract_command_name(func_name, func),
            description=self._extract_description(func),
            category=self._extract_category(module_name),
            aliases=self._extract_aliases(func),
            parameters=self._extract_parameters(func),
            examples=self._extract_examples(func),
            tags=self._extract_tags(func),
            requires_project=self._extract_requires_project(func),
            hidden=self._extract_hidden(func)
        )

        return metadata

    def _extract_description(self, func: Callable) -> str:
        """Extract command description"""
        if hasattr(func, '_command_description'):
            return getattr(func, '_command_description')

        if hasattr(func, '__doc__') and func.__doc__:
            # Get first line of docstring
            docstring = func.__doc__.strip()
            first_line = docstring.split('\n')[0].strip()
            return first_line

        # Default description
        return f"Execute {func.__name__} command"

    def _extract_category(self, module_name: str) -> str:
        """Extract command category from module name"""
        # Map module names to categories
        category_map = {
            'spec_command': 'specification',
            'plan_command': 'planning',
            'tasks_command': 'task-management',
            'research_command': 'research',
            'analyze_command': 'analysis',
            'migrate_command': 'migration'
        }

        for key, category in category_map.items():
            if key in module_name:
                return category

        return 'general'

    def _extract_aliases(self, func: Callable) -> List[str]:
        """Extract command aliases"""
        if hasattr(func, '_command_aliases'):
            return getattr(func, '_command_aliases')

        return []

    def _extract_parameters(self, func: Callable) -> Dict[str, Any]:
        """Extract command parameters from function signature"""
        try:
            sig = inspect.signature(func)
            parameters = {}

            for param_name, param in sig.parameters.items():
                if param_name in ['args', 'kwargs']:
                    continue

                param_info = {
                    'type': str(param.annotation) if param.annotation != param.empty else 'any',
                    'default': str(param.default) if param.default != param.empty else None,
                    'required': param.default == param.empty
                }
                parameters[param_name] = param_info

            return parameters
        except Exception:
            return {}

    def _extract_examples(self, func: Callable) -> List[str]:
        """Extract command examples"""
        if hasattr(func, '_command_examples'):
            return getattr(func, '_command_examples')

        return []

    def _extract_tags(self, func: Callable) -> List[str]:
        """Extract command tags"""
        tags = []

        # Add tags based on function attributes
        if hasattr(func, '_command_tags'):
            tags.extend(getattr(func, '_command_tags'))

        # Add tags based on module
        module_name = getattr(func, '__module__', '')
        if 'spec' in module_name.lower():
            tags.append('specification')
        if 'plan' in module_name.lower():
            tags.append('planning')
        if 'task' in module_name.lower():
            tags.append('task-management')
        if 'research' in module_name.lower():
            tags.append('research')
        if 'analyze' in module_name.lower():
            tags.append('analysis')
        if 'migrate' in module_name.lower():
            tags.append('migration')

        return list(set(tags))  # Remove duplicates

    def _extract_requires_project(self, func: Callable) -> bool:
        """Extract whether command requires a project context"""
        if hasattr(func, '_requires_project'):
            return getattr(func, '_requires_project')

        # Check function name for clues
        func_name = getattr(func, '__name__', '').lower()
        if any(keyword in func_name for keyword in ['project', 'workspace', 'git']):
            return True

        return False

    def _extract_hidden(self, func: Callable) -> bool:
        """Extract whether command should be hidden"""
        if hasattr(func, '_command_hidden'):
            return getattr(func, '_command_hidden')

        # Check function name for clues
        func_name = getattr(func, '__name__', '').lower()
        if func_name.startswith('_') or 'internal' in func_name:
            return True

        return False

    def register_discovered_commands(self) -> int:
        """Register all discovered commands with the registry"""
        registered_count = 0

        for command in self.discovered_commands.values():
            try:
                if command.metadata:
                    self.registry.register_command(
                        name=command.name,
                        handler=command.handler,
                        description=command.metadata.description,
                        category=command.metadata.category,
                        aliases=command.metadata.aliases,
                        parameters=command.metadata.parameters,
                        examples=command.metadata.examples,
                        tags=command.metadata.tags,
                        requires_project=command.metadata.requires_project,
                        hidden=command.metadata.hidden
                    )
                else:
                    # Register with minimal metadata
                    self.registry.register_command(
                        name=command.name,
                        handler=command.handler,
                        description=f"Execute {command.name} command",
                        category='general'
                    )
                registered_count += 1
            except Exception as e:
                print(f"Warning: Could not register command {command.name}: {e}")

        return registered_count

    def get_discovered_commands(self) -> List[DiscoveredCommand]:
        """Get all discovered commands"""
        return list(self.discovered_commands.values())

    def get_discovered_command(self, name: str) -> Optional[DiscoveredCommand]:
        """Get a specific discovered command"""
        return self.discovered_commands.get(name)

    def clear_discovered_commands(self) -> None:
        """Clear all discovered commands"""
        self.discovered_commands.clear()

    def discover_and_register(self, base_module: str = "specify_cli.opencode.commands") -> Dict[str, Any]:
        """Discover and register commands in one operation"""
        # Clear previous discoveries
        self.clear_discovered_commands()

        # Discover commands
        discovered = self.discover_commands(base_module)

        # Register commands
        registered_count = self.register_discovered_commands()

        return {
            'discovered_count': len(discovered),
            'registered_count': registered_count,
            'commands': [cmd.name for cmd in discovered]
        }