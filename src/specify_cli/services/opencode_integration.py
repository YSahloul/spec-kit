"""
OpenCodeIntegration - Integration layer for OpenCode command system
"""

import json
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import jsonschema

from specify_cli.services.command_registry import CommandRegistry
from specify_cli.services.command_discovery import CommandDiscovery
from specify_cli.services.command_executor import CommandExecutor
from specify_cli.services.command_help import CommandHelp
from specify_cli.services.configuration_service import ConfigurationService
from specify_cli.services.agent_registry import AgentRegistry
from rich.console import Console

console = Console()


class OpenCodeIntegration:
    """Integration layer for connecting spec-kit with OpenCode"""

    def __init__(self, config_service: Optional[ConfigurationService] = None):
        self.config_service = config_service or ConfigurationService()
        self.registry = CommandRegistry(self.config_service)
        self.discovery = CommandDiscovery(self.registry)
        self.executor = CommandExecutor(self.registry, self.config_service)
        self.help_system = CommandHelp(self.registry)
        self.agent_registry = AgentRegistry(self.config_service)

        # Integration state
        self._initialized = False
        self._opencode_commands = {}
        self._opencode_agents = {}

        # Schema validation integration
        self._schema_registered = False
        self._validation_hooks = {}

    def initialize(self, opencode_available: bool = True) -> Dict[str, Any]:
        """Initialize the spec-kit integration with OpenCode"""
        if self._initialized:
            return {'status': 'already_initialized'}

        try:
            # Discover and register commands
            discovery_result = self.discovery.discover_and_register()

            # Initialize agent registry
            agent_result = self.agent_registry.initialize()

            # Set up OpenCode command mappings (only if OpenCode is available)
            if opencode_available:
                self._setup_opencode_commands()
                self._setup_opencode_agents()
                self._register_schema_validation()
            else:
                # Set up standalone mode
                self._setup_standalone_commands()
                console.print("[cyan]ℹ️  Running in standalone mode - OpenCode CLI integration disabled[/cyan]")

            self._initialized = True

            return {
                'status': 'success',
                'commands_discovered': discovery_result['discovered_count'],
                'commands_registered': discovery_result['registered_count'],
                'agents_discovered': agent_result['agents_discovered'],
                'agents_registered': agent_result['agents_registered'],
                'opencode_commands': len(self._opencode_commands) if opencode_available else 0,
                'opencode_agents': len(self._opencode_agents) if opencode_available else 0,
                'standalone_mode': not opencode_available
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def _setup_opencode_commands(self) -> None:
        """Set up OpenCode command mappings"""
        # Core spec-kit commands
        self._opencode_commands = {
            # Help and information commands
            'help': self._create_opencode_command('help', self._handle_help_command),
            'commands': self._create_opencode_command('commands', self._handle_commands_command),
            'search': self._create_opencode_command('search', self._handle_search_command),

            # Spec-kit specific commands
            'spec': self._create_opencode_command('spec', self._handle_spec_command),
            'plan': self._create_opencode_command('plan', self._handle_plan_command),
            'tasks': self._create_opencode_command('tasks', self._handle_tasks_command),
            'research': self._create_opencode_command('research', self._handle_research_command),
            'analyze': self._create_opencode_command('analyze', self._handle_analyze_command),
            'migrate': self._create_opencode_command('migrate', self._handle_migrate_command),

            # Configuration commands
            'config': self._create_opencode_command('config', self._handle_config_command),
            'status': self._create_opencode_command('status', self._handle_status_command),
        }

    def _setup_opencode_agents(self) -> None:
        """Set up OpenCode agent mappings"""
        # Get all registered agents
        agents = self.agent_registry.list_agents()

        # Create agent mappings
        self._opencode_agents = {}
        for agent_info in agents:
            agent_name = agent_info['name']
            self._opencode_agents[agent_name] = self._create_opencode_agent(agent_name, agent_info)

    def _create_opencode_command(self, name: str, handler: Callable) -> Dict[str, Any]:
        """Create an OpenCode-compatible command definition"""
        return {
            'name': name,
            'handler': handler,
            'description': f"Spec-kit {name} command",
            'category': 'spec-kit',
            'requires_project': self._command_requires_project(name),
            'hidden': False,
        }

    def _create_opencode_agent(self, name: str, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create an OpenCode-compatible agent definition"""
        return {
            'name': name,
            'handler': self._handle_agent_execution,
            'description': agent_info.get('description', f"{name} agent"),
            'category': 'spec-kit-agent',
            'capabilities': agent_info.get('capabilities', []),
            'metadata': agent_info,
            'requires_project': True,
            'hidden': False,
        }

    def _command_requires_project(self, command_name: str) -> bool:
        """Check if a command requires a project context"""
        project_commands = ['spec', 'plan', 'tasks', 'analyze', 'migrate']
        return command_name in project_commands

    def get_opencode_commands(self) -> Dict[str, Any]:
        """Get all OpenCode-compatible command definitions"""
        if not self._initialized:
            self.initialize()

        return self._opencode_commands.copy()

    def execute_opencode_command(
        self,
        command_name: str,
        args: Optional[List[str]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute an OpenCode command"""
        if not self._initialized:
            init_result = self.initialize()
            if init_result['status'] != 'success':
                return {
                    'success': False,
                    'error': f'Failed to initialize: {init_result.get("error", "Unknown error")}'
                }

        # Check if it's a direct spec-kit command
        if command_name in self._opencode_commands:
            try:
                handler = self._opencode_commands[command_name]['handler']
                result = handler(args or [], kwargs or {}, context or {})
                return {
                    'success': True,
                    'result': result,
                    'command': command_name
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'command': command_name
                }

        # Try to execute as a registered command
        try:
            result = self.executor.execute_string(f"/{command_name} {' '.join(args or [])}", context)
            return {
                'success': result.success,
                'result': result.output if result.success else None,
                'error': result.error if not result.success else None,
                'command': command_name,
                'execution_time': result.execution_time
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command': command_name
            }

    def get_command_help(self, command_name: str) -> Dict[str, Any]:
        """Get help for an OpenCode command"""
        if command_name in self._opencode_commands:
            cmd_def = self._opencode_commands[command_name]
            return {
                'name': command_name,
                'description': cmd_def['description'],
                'category': cmd_def['category'],
                'requires_project': cmd_def['requires_project'],
                'usage': self._get_command_usage(command_name)
            }

        # Try to get help from the registry
        help_info = self.registry.get_command_help(command_name)
        if help_info:
            return help_info

        return {
            'name': command_name,
            'description': f'Unknown command: {command_name}',
            'error': 'Command not found'
        }

    def _get_command_usage(self, command_name: str) -> str:
        """Get usage string for a command"""
        usage_map = {
            'help': '/help [command] - Show help for commands',
            'commands': '/commands [category] - List available commands',
            'search': '/search <query> - Search for commands',
            'spec': '/spec <description> [--template=name] - Create a specification',
            'plan': '/plan [--from-spec=id] - Generate implementation plan',
            'tasks': '/tasks [--list] - Manage development tasks',
            'research': '/research <topic> - Research technical topics',
            'analyze': '/analyze <path> - Analyze codebase',
            'migrate': '/migrate <source> - Migrate existing code',
            'config': '/config - Show configuration',
            'status': '/status - Show system status'
        }

        return usage_map.get(command_name, f'/{command_name} - {command_name} command')

    def get_completion_suggestions(self, partial_command: str) -> List[str]:
        """Get completion suggestions for partial commands"""
        suggestions = []

        # Add OpenCode commands
        for cmd_name in self._opencode_commands.keys():
            if cmd_name.startswith(partial_command):
                suggestions.append(cmd_name)

        # Add registered commands
        registry_suggestions = self.executor.get_command_suggestions(partial_command)
        suggestions.extend(registry_suggestions)

        return list(set(suggestions))  # Remove duplicates

    def get_system_status(self) -> Dict[str, Any]:
        """Get the current system status"""
        if not self._initialized:
            return {'status': 'not_initialized'}

        registry_stats = self.registry.get_stats()

        return {
            'status': 'initialized',
            'registry_stats': registry_stats,
            'opencode_commands': len(self._opencode_commands),
            'configuration_valid': self._check_configuration_status()
        }

    def _check_configuration_status(self) -> bool:
        """Check if configuration is valid"""
        try:
            # Check global config
            global_config = self.config_service.load_global_config()
            if not global_config.version:
                return False

            # Check if we're in a project context
            current_dir = Path.cwd()
            if (current_dir / '.opencode').exists():
                project_config = self.config_service.load_project_config(str(current_dir))
                if not project_config.project_path:
                    return False

            return True
        except Exception:
            return False

    # Command handlers
    def _handle_help_command(self, args: List[str], kwargs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle /help command"""
        if args:
            command_name = args[0]
            self.help_system.show_command_help(command_name)
            return f"Help displayed for command: {command_name}"
        else:
            self.help_system.show_help_overview()
            return "General help displayed"

    def _handle_commands_command(self, args: List[str], kwargs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle /commands command"""
        if args:
            category = args[0]
            self.help_system.show_category_help(category)
            return f"Commands displayed for category: {category}"
        else:
            self.help_system.show_available_commands()
            return "All available commands displayed"

    def _handle_search_command(self, args: List[str], kwargs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle /search command"""
        if not args:
            return "Error: Please provide a search query"

        query = args[0]
        self.help_system.search_commands(query)
        return f"Search results displayed for: {query}"

    def _handle_spec_command(self, args: List[str], kwargs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle /spec command"""
        if not args:
            return "Error: Please provide a specification description"

        description = args[0]
        template = kwargs.get('template', 'default')

        # This would integrate with the actual spec generation service
        return f"Specification created: '{description}' (template: {template})"

    def _handle_plan_command(self, args: List[str], kwargs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle /plan command"""
        spec_id = kwargs.get('from_spec')
        if spec_id:
            return f"Implementation plan generated for spec: {spec_id}"
        else:
            return "Implementation plan generated"

    def _handle_tasks_command(self, args: List[str], kwargs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle /tasks command"""
        if kwargs.get('list'):
            return "Task list displayed"
        else:
            return "Task management interface opened"

    def _handle_research_command(self, args: List[str], kwargs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle /research command"""
        if not args:
            return "Error: Please provide a research topic"

        topic = args[0]
        return f"Research initiated for topic: {topic}"

    def _handle_analyze_command(self, args: List[str], kwargs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle /analyze command"""
        if not args:
            return "Error: Please provide a path to analyze"

        path = args[0]
        return f"Codebase analysis started for: {path}"

    def _handle_migrate_command(self, args: List[str], kwargs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle /migrate command"""
        if not args:
            return "Error: Please provide a source to migrate"

        source = args[0]
        return f"Migration started for: {source}"

    def _handle_config_command(self, args: List[str], kwargs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle /config command"""
        # This would show configuration information
        return "Configuration displayed"

    def _handle_status_command(self, args: List[str], kwargs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle /status command"""
        status = self.get_system_status()
        return f"System status: {json.dumps(status, indent=2)}"

    def _handle_agent_execution(self, agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent execution"""
        return self.agent_registry.execute_agent(agent_name, input_data)

    def get_opencode_agents(self) -> Dict[str, Any]:
        """Get all OpenCode-compatible agent definitions"""
        if not self._initialized:
            self.initialize()

        return self._opencode_agents.copy()

    def execute_opencode_agent(
        self,
        agent_name: str,
        input_data: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute an OpenCode agent"""
        if not self._initialized:
            init_result = self.initialize()
            if init_result['status'] != 'success':
                return {
                    'success': False,
                    'error': f'Failed to initialize: {init_result.get("error", "Unknown error")}'
                }

        # Check if it's a direct spec-kit agent
        if agent_name in self._opencode_agents:
            try:
                result = self._handle_agent_execution(agent_name, input_data or {})
                return {
                    'success': result['success'],
                    'result': result.get('result'),
                    'error': result.get('error'),
                    'agent': agent_name,
                    'execution_time': result.get('timestamp')
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'agent': agent_name
                }

        return {
            'success': False,
            'error': f'Agent "{agent_name}" not found',
            'agent': agent_name
        }

    def get_agent_help(self, agent_name: str) -> Dict[str, Any]:
        """Get help for an OpenCode agent"""
        if agent_name in self._opencode_agents:
            agent_def = self._opencode_agents[agent_name]
            metadata = self.agent_registry.get_agent_metadata(agent_name) or {}

            return {
                'name': agent_name,
                'description': agent_def['description'],
                'capabilities': agent_def['capabilities'],
                'version': metadata.get('version', '1.0.0'),
                'author': metadata.get('author', 'spec-kit'),
                'supported_actions': metadata.get('supported_actions', []),
                'input_schema': metadata.get('input_schema', {})
            }

        return {
            'name': agent_name,
            'description': f'Unknown agent: {agent_name}',
            'error': 'Agent not found'
        }

    def get_agent_status_summary(self) -> Dict[str, Any]:
        """Get status summary of all agents"""
        if not self._initialized:
            return {'status': 'not_initialized'}

        agent_statuses = self.agent_registry.get_all_agent_statuses()

        summary = {
            'total_agents': len(agent_statuses),
            'active_agents': sum(1 for s in agent_statuses if s['status'] == 'active'),
            'inactive_agents': sum(1 for s in agent_statuses if s['status'] == 'inactive'),
            'error_agents': sum(1 for s in agent_statuses if s['status'] == 'error'),
            'agent_details': agent_statuses
        }

        return summary

    def create_opencode_plugin(self) -> Dict[str, Any]:
        """Create an OpenCode plugin definition"""
        return {
            'name': 'spec-kit',
            'version': '1.0.0',
            'description': 'OpenCode Spec-Driven Development Toolkit',
            'commands': self.get_opencode_commands(),
            'agents': self.get_opencode_agents(),
            'hooks': {
                'on_project_init': self._on_project_init,
                'on_command_execute': self._on_command_execute,
                'on_config_change': self._on_config_change,
                'on_agent_execute': self._on_agent_execute
            },
            'validation': {
                'schema_registered': self._schema_registered,
                'validation_hooks': list(self._validation_hooks.keys()) if self._validation_hooks else [],
                'supported_config_types': ['opencode', 'project'],
                'schema_info': self.get_schema_information() if self._schema_registered else None
            },
            'capabilities': [
                'specification-management',
                'implementation-planning',
                'task-management',
                'research-capabilities',
                'code-analysis',
                'migration-support',
                'agent-execution',
                'spec-driven-development',
                'json-schema-validation',
                'configuration-validation',
                'project-validation'
            ]
        }

    def _on_agent_execute(self, agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Hook called when an agent is executed"""
        # Could be used for logging, analytics, etc.
        return self.execute_opencode_agent(agent_name, input_data)

    def _on_project_init(self, project_path: str) -> None:
        """Hook called when a new project is initialized"""
        try:
            # Set up project configuration
            self.config_service.load_project_config(project_path)
        except Exception as e:
            print(f"Warning: Failed to initialize spec-kit for project: {e}")

    def _on_command_execute(self, command_name: str, result: Any) -> None:
        """Hook called after command execution"""
        # Could be used for logging, analytics, etc.
        pass

    def _on_config_change(self, config_type: str, changes: Dict[str, Any]) -> None:
        """Hook called when configuration changes"""
        # Could be used to update cached configurations
        if config_type == 'global':
            self.config_service.clear_cache()

    def _register_schema_validation(self) -> None:
        """Register spec-kit schema with OpenCode's validation system"""
        if self._schema_registered:
            return

        try:
            # Get the spec-kit schema
            schema = self.config_service._schema

            # Register validation hooks
            self._validation_hooks = {
                'validate_config': self._validate_config_hook,
                'validate_project_config': self._validate_project_config_hook,
                'get_schema_info': self._get_schema_info_hook
            }

            self._schema_registered = True

        except Exception as e:
            # Schema registration failed, but don't break initialization
            print(f"Warning: Failed to register spec-kit schema: {e}")

    def _validate_config_hook(self, config_data: Dict[str, Any], config_type: str = "global") -> Dict[str, Any]:
        """Hook for validating configuration data"""
        return self.config_service.validate_configuration_data(config_data, config_type)

    def _validate_project_config_hook(self, project_path: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Hook for validating project configuration data"""
        # First validate the data structure
        validation_result = self.config_service.validate_configuration_data(config_data, "project")

        if not validation_result["valid"]:
            return validation_result

        # Additional project-specific validation
        issues = []

        # Check if project path exists
        if not Path(project_path).exists():
            issues.append(f"Project path does not exist: {project_path}")

        # Check if .opencode directory exists for spec-kit
        opencode_dir = Path(project_path) / ".opencode" / "spec-kit"
        if not opencode_dir.exists():
            issues.append(f"Spec-kit directory not found: {opencode_dir}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "config_type": "project",
            "project_path": project_path
        }

    def _get_schema_info_hook(self) -> Dict[str, Any]:
        """Hook for getting schema information"""
        schema = self.config_service._schema

        return {
            "schema_version": schema.get("$schema", "http://json-schema.org/draft-07/schema#"),
            "title": schema.get("title", "Spec-Kit Configuration Schema"),
            "description": schema.get("description", "JSON schema for validating spec-kit configuration files"),
            "definitions": list(schema.get("definitions", {}).keys()),
            "supported_config_types": ["opencode", "project"]
        }

    def validate_opencode_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate OpenCode configuration data against spec-kit schema"""
        if not self._schema_registered:
            self._register_schema_validation()

        return self._validate_config_hook(config_data, "global")

    def validate_project_config(self, project_path: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate project configuration data against spec-kit schema"""
        if not self._schema_registered:
            self._register_schema_validation()

        return self._validate_project_config_hook(project_path, config_data)

    def get_schema_information(self) -> Dict[str, Any]:
        """Get information about the spec-kit schema"""
        if not self._schema_registered:
            self._register_schema_validation()

        return self._get_schema_info_hook()

    def register_validation_callbacks(self, callback_registry: Dict[str, Callable]) -> None:
        """Register validation callbacks with OpenCode's callback system"""
        if not self._schema_registered:
            self._register_schema_validation()

        # Register our validation hooks
        for hook_name, hook_func in self._validation_hooks.items():
            callback_registry[hook_name] = hook_func

    def get_validation_status(self) -> Dict[str, Any]:
        """Get the current validation system status"""
        return {
            "schema_registered": self._schema_registered,
            "validation_hooks_available": len(self._validation_hooks),
            "schema_info": self.get_schema_information() if self._schema_registered else None
        }