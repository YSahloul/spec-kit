"""
CommandExecutor - Framework for executing OpenCode commands
"""

import re
import shlex
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from specify_cli.services.command_registry import CommandRegistry
from specify_cli.services.configuration_service import ConfigurationService


@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    command_name: str = ""
    execution_time: float = 0.0
    context: Optional[Dict[str, Any]] = None


@dataclass
class ParsedCommand:
    """Parsed command with arguments"""
    name: str
    args: List[str]
    kwargs: Dict[str, Any]
    raw_input: str


class CommandExecutor:
    """Framework for executing OpenCode commands"""

    def __init__(
        self,
        registry: CommandRegistry,
        config_service: Optional[ConfigurationService] = None
    ):
        self.registry = registry
        self.config_service = config_service or ConfigurationService()

    def execute_string(self, command_string: str, context: Optional[Dict[str, Any]] = None) -> CommandResult:
        """Execute a command from string input"""
        import time
        start_time = time.time()

        try:
            # Parse the command string
            parsed = self.parse_command_string(command_string)
            if not parsed:
                return CommandResult(
                    success=False,
                    error="Failed to parse command",
                    command_name="",
                    execution_time=time.time() - start_time
                )

            # Execute the parsed command
            result = self.execute_parsed_command(parsed, context)

            # Add execution time
            result.execution_time = time.time() - start_time
            result.context = context

            return result

        except Exception as e:
            return CommandResult(
                success=False,
                error=str(e),
                command_name="",
                execution_time=time.time() - start_time,
                context=context
            )

    def execute_parsed_command(
        self,
        parsed: ParsedCommand,
        context: Optional[Dict[str, Any]] = None
    ) -> CommandResult:
        """Execute a parsed command"""
        try:
            # Validate command exists
            command = self.registry.get_command(parsed.name)
            if not command:
                return CommandResult(
                    success=False,
                    error=f"Command '{parsed.name}' not found",
                    command_name=parsed.name
                )

            # Validate command is enabled
            if not command.enabled:
                return CommandResult(
                    success=False,
                    error=f"Command '{parsed.name}' is disabled",
                    command_name=parsed.name
                )

            # Validate project context if required
            if command.metadata.requires_project:
                if not context or not context.get('project_path'):
                    return CommandResult(
                        success=False,
                        error=f"Command '{parsed.name}' requires a project context",
                        command_name=parsed.name
                    )

            # Validate arguments
            validation_result = self.validate_command_arguments(parsed, command)
            if not validation_result['valid']:
                return CommandResult(
                    success=False,
                    error=validation_result['error'],
                    command_name=parsed.name
                )

            # Execute the command
            result = self.registry.execute_command(
                parsed.name,
                args=parsed.args,
                kwargs=parsed.kwargs,
                context=context
            )

            return CommandResult(
                success=True,
                output=result,
                command_name=parsed.name
            )

        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Command execution failed: {str(e)}",
                command_name=parsed.name
            )

    def parse_command_string(self, command_string: str) -> Optional[ParsedCommand]:
        """Parse a command string into components"""
        if not command_string or not command_string.strip():
            return None

        # Remove leading/trailing whitespace
        command_string = command_string.strip()

        # Handle different command formats
        if command_string.startswith('/'):
            # OpenCode style: /command arg1 arg2 --flag=value
            return self._parse_opencode_command(command_string)
        else:
            # Try to parse as regular command
            return self._parse_simple_command(command_string)

    def _parse_opencode_command(self, command_string: str) -> Optional[ParsedCommand]:
        """Parse OpenCode style command: /command arg1 arg2 --flag=value"""
        # Remove the leading /
        cmd_part = command_string[1:]

        # Split into command name and arguments
        parts = shlex.split(cmd_part)
        if not parts:
            return None

        command_name = parts[0]
        args = []
        kwargs = {}

        # Parse arguments and flags
        i = 1
        while i < len(parts):
            part = parts[i]

            if part.startswith('--'):
                # Long flag: --flag=value or --flag value
                flag_part = part[2:]
                if '=' in flag_part:
                    key, value = flag_part.split('=', 1)
                    kwargs[key] = self._parse_value(value)
                else:
                    # Next part should be the value
                    if i + 1 < len(parts):
                        kwargs[flag_part] = self._parse_value(parts[i + 1])
                        i += 1  # Skip the value
                    else:
                        kwargs[flag_part] = True
            elif part.startswith('-'):
                # Short flag: -f value or -f
                flag_name = part[1:]
                if i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                    kwargs[flag_name] = self._parse_value(parts[i + 1])
                    i += 1  # Skip the value
                else:
                    kwargs[flag_name] = True
            else:
                # Regular argument
                args.append(self._parse_value(part))

            i += 1

        return ParsedCommand(
            name=command_name,
            args=args,
            kwargs=kwargs,
            raw_input=command_string
        )

    def _parse_simple_command(self, command_string: str) -> Optional[ParsedCommand]:
        """Parse simple command format"""
        parts = shlex.split(command_string)
        if not parts:
            return None

        return ParsedCommand(
            name=parts[0],
            args=[self._parse_value(p) for p in parts[1:]],
            kwargs={},
            raw_input=command_string
        )

    def _parse_value(self, value: str) -> Any:
        """Parse a string value into appropriate type"""
        # Try to parse as boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # Try to parse as number
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Try to parse as None
        if value.lower() in ('none', 'null'):
            return None

        # Return as string
        return value

    def validate_command_arguments(self, parsed: ParsedCommand, command) -> Dict[str, Any]:
        """Validate command arguments against metadata"""
        if not command.metadata.parameters:
            return {'valid': True}

        errors = []

        # Check required parameters
        for param_name, param_info in command.metadata.parameters.items():
            if param_info.get('required', False):
                if param_name not in parsed.kwargs and len(parsed.args) == 0:
                    errors.append(f"Required parameter '{param_name}' is missing")

        # Check parameter types
        for param_name, value in parsed.kwargs.items():
            if param_name in command.metadata.parameters:
                param_info = command.metadata.parameters[param_name]
                expected_type = param_info.get('type', 'any')

                if not self._validate_type(value, expected_type):
                    errors.append(f"Parameter '{param_name}' should be of type {expected_type}")

        if errors:
            return {
                'valid': False,
                'error': '; '.join(errors)
            }

        return {'valid': True}

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type"""
        type_map = {
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict
        }

        if expected_type == 'any':
            return True

        expected_python_type = type_map.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)

        return True  # Unknown type, assume valid

    def get_command_suggestions(self, partial_command: str) -> List[str]:
        """Get command suggestions for partial input"""
        if not partial_command:
            return []

        # Get all available commands
        commands = self.registry.list_commands(include_hidden=False)
        command_names = [cmd.metadata.name for cmd in commands]

        # Filter by partial match
        suggestions = []
        for name in command_names:
            if name.startswith(partial_command):
                suggestions.append(name)

        return suggestions

    def get_command_completion(self, command_name: str, current_arg: str) -> List[str]:
        """Get completion suggestions for command arguments"""
        command = self.registry.get_command(command_name)
        if not command or not command.metadata.parameters:
            return []

        # Get parameter names that match current argument
        suggestions = []
        for param_name in command.metadata.parameters.keys():
            if param_name.startswith(current_arg):
                suggestions.append(f"--{param_name}")

        return suggestions

    def create_execution_context(
        self,
        project_path: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create execution context for commands"""
        context = {
            'timestamp': None,  # Will be set when command executes
            'user_id': user_id,
            'session_id': session_id,
        }

        if project_path:
            context['project_path'] = Path(project_path).resolve()

            # Add project configuration if available
            try:
                project_config = self.config_service.load_project_config(project_path)
                context['project_config'] = project_config
            except Exception:
                pass  # Ignore config loading errors

        return context

    def format_result(self, result: CommandResult) -> str:
        """Format command result for display"""
        if result.success:
            if result.output is not None:
                return str(result.output)
            else:
                return f"Command '{result.command_name}' executed successfully"
        else:
            return f"Error executing '{result.command_name}': {result.error}"

    def get_execution_history(self) -> List[CommandResult]:
        """Get execution history (placeholder for future implementation)"""
        # This would be implemented with persistent storage
        return []

    def clear_execution_history(self) -> None:
        """Clear execution history"""
        # This would be implemented with persistent storage
        pass