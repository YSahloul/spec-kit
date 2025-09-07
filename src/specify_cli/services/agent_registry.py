"""
Agent Registry - Manages spec-kit agents for OpenCode integration
"""

import importlib
import inspect
from typing import Dict, List, Any, Optional, Type
from pathlib import Path
from datetime import datetime

from specify_cli.services.configuration_service import ConfigurationService


class AgentRegistry:
    """Registry for managing spec-kit agents"""

    def __init__(self, config_service: Optional[ConfigurationService] = None):
        self.config_service = config_service or ConfigurationService()
        self._agents = {}  # name -> agent instance
        self._agent_classes = {}  # name -> agent class
        self._agent_metadata = {}  # name -> metadata
        self._initialized = False

    def initialize(self) -> Dict[str, Any]:
        """Initialize the agent registry"""
        if self._initialized:
            return {'status': 'already_initialized'}

        try:
            # Discover and register agents
            discovery_result = self._discover_agents()

            # Initialize agent instances
            init_result = self._initialize_agents()

            self._initialized = True

            return {
                'status': 'success',
                'agents_discovered': discovery_result['discovered_count'],
                'agents_registered': discovery_result['registered_count'],
                'agents_initialized': init_result['initialized_count']
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def _discover_agents(self) -> Dict[str, Any]:
        """Discover available agents"""
        discovered_count = 0
        registered_count = 0

        # Get agent directory path
        agent_dir = Path(__file__).parent.parent / 'opencode' / 'agents'

        if not agent_dir.exists():
            return {'discovered_count': 0, 'registered_count': 0}

        # Find all agent Python files
        for agent_file in agent_dir.glob('*.py'):
            if agent_file.name.startswith('__'):
                continue

            try:
                # Import the agent module
                module_name = f"specify_cli.opencode.agents.{agent_file.stem}"
                module = importlib.import_module(module_name)

                # Find agent classes in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and
                        hasattr(obj, 'execute') and
                        hasattr(obj, 'get_capabilities') and
                        name.endswith('Agent')):

                        agent_name = obj().name if hasattr(obj, 'name') else name.lower().replace('agent', '')

                        # Register the agent class
                        self._agent_classes[agent_name] = obj

                        # Extract metadata
                        self._agent_metadata[agent_name] = self._extract_agent_metadata(obj)

                        discovered_count += 1
                        registered_count += 1

            except Exception as e:
                print(f"Warning: Failed to load agent from {agent_file}: {e}")
                continue

        return {
            'discovered_count': discovered_count,
            'registered_count': registered_count
        }

    def _extract_agent_metadata(self, agent_class: Type) -> Dict[str, Any]:
        """Extract metadata from agent class"""
        # Create a temporary instance to get metadata
        try:
            temp_instance = agent_class()
            metadata = {
                'name': getattr(temp_instance, 'name', agent_class.__name__.lower().replace('agent', '')),
                'description': getattr(temp_instance, 'description', f"{agent_class.__name__} agent"),
                'capabilities': getattr(temp_instance, 'capabilities', []),
                'version': getattr(temp_instance, 'version', '1.0.0'),
                'author': getattr(temp_instance, 'author', 'spec-kit'),
                'class_name': agent_class.__name__,
                'module': agent_class.__module__
            }
            return metadata
        except Exception:
            return {
                'name': agent_class.__name__.lower().replace('agent', ''),
                'description': f"{agent_class.__name__} agent",
                'capabilities': [],
                'version': '1.0.0',
                'author': 'spec-kit',
                'class_name': agent_class.__name__,
                'module': agent_class.__module__
            }

    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize agent instances"""
        initialized_count = 0

        for agent_name, agent_class in self._agent_classes.items():
            try:
                # Create agent instance
                agent_instance = agent_class()

                # Store the instance
                self._agents[agent_name] = agent_instance

                initialized_count += 1

            except Exception as e:
                print(f"Warning: Failed to initialize agent {agent_name}: {e}")
                continue

        return {'initialized_count': initialized_count}

    def get_agent(self, name: str) -> Optional[Any]:
        """Get an agent instance by name"""
        return self._agents.get(name)

    def get_agent_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get agent metadata by name"""
        return self._agent_metadata.get(name)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        agents = []
        for name, metadata in self._agent_metadata.items():
            agent_info = metadata.copy()
            agent_info['status'] = 'active' if name in self._agents else 'inactive'
            agents.append(agent_info)

        return agents

    def execute_agent(self, agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an agent with given input"""
        agent = self.get_agent(agent_name)
        if not agent:
            return {
                'success': False,
                'error': f'Agent "{agent_name}" not found'
            }

        try:
            result = agent.execute(input_data)
            return {
                'success': True,
                'result': result,
                'agent': agent_name,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'agent': agent_name,
                'timestamp': datetime.now().isoformat()
            }

    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get status of a specific agent"""
        agent = self.get_agent(agent_name)
        if not agent:
            return {
                'name': agent_name,
                'status': 'not_found'
            }

        try:
            if hasattr(agent, 'get_status'):
                status = agent.get_status()
            else:
                status = {
                    'name': agent_name,
                    'status': 'active',
                    'capabilities': getattr(agent, 'capabilities', []),
                    'last_active': datetime.now().isoformat()
                }
        except Exception as e:
            status = {
                'name': agent_name,
                'status': 'error',
                'error': str(e)
            }

        return status

    def get_all_agent_statuses(self) -> List[Dict[str, Any]]:
        """Get status of all agents"""
        statuses = []
        for agent_name in self._agent_metadata.keys():
            statuses.append(self.get_agent_status(agent_name))

        return statuses

    def reload_agent(self, agent_name: str) -> Dict[str, Any]:
        """Reload a specific agent"""
        if agent_name not in self._agent_classes:
            return {
                'success': False,
                'error': f'Agent "{agent_name}" not found in registry'
            }

        try:
            agent_class = self._agent_classes[agent_name]
            new_instance = agent_class()
            self._agents[agent_name] = new_instance

            return {
                'success': True,
                'agent': agent_name,
                'message': f'Agent "{agent_name}" reloaded successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'agent': agent_name
            }

    def get_capabilities_summary(self) -> Dict[str, List[str]]:
        """Get summary of all agent capabilities"""
        summary = {}
        for agent_name, metadata in self._agent_metadata.items():
            summary[agent_name] = metadata.get('capabilities', [])

        return summary

    def search_agents(self, query: str) -> List[Dict[str, Any]]:
        """Search agents by name or capabilities"""
        results = []
        query_lower = query.lower()

        for name, metadata in self._agent_metadata.items():
            if (query_lower in name.lower() or
                query_lower in metadata.get('description', '').lower() or
                any(query_lower in cap.lower() for cap in metadata.get('capabilities', []))):

                agent_info = metadata.copy()
                agent_info['status'] = 'active' if name in self._agents else 'inactive'
                results.append(agent_info)

        return results