"""
ConfigurationService - Manages spec-kit configuration for OpenCode integration
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, Union, List
from dataclasses import asdict
from datetime import datetime
import jsonschema

from specify_cli.models.opencode_config import OpenCodeConfig
from specify_cli.models.project_configuration import ProjectConfiguration


class ConfigurationService:
    """Service for managing spec-kit configuration with OpenCode integration"""

    def __init__(self):
        self.global_config_dir = Path.home() / ".config" / "opencode" / "spec-kit"
        self.global_config_file = self.global_config_dir / "config.json"
        self.state_file = self.global_config_dir / "state.json"

        # Cache for loaded configurations
        self._global_config: Optional[OpenCodeConfig] = None
        self._project_configs: Dict[str, ProjectConfiguration] = {}

        # Load schema for validation
        self._schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        """Load the JSON schema for configuration validation"""
        schema_path = Path(__file__).parent / "config_schema.json"
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return minimal schema if file not found
            return {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "additionalProperties": True
            }

    def ensure_global_config_dir(self) -> None:
        """Ensure global configuration directory exists"""
        self.global_config_dir.mkdir(parents=True, exist_ok=True)

    def load_global_config(self) -> OpenCodeConfig:
        """Load global OpenCode configuration"""
        if self._global_config is not None:
            return self._global_config

        self.ensure_global_config_dir()

        if self.global_config_file.exists():
            try:
                with open(self.global_config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._global_config = OpenCodeConfig.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                # If config is corrupted, create default
                self._global_config = OpenCodeConfig()
                self.save_global_config()
        else:
            # Create default configuration
            self._global_config = OpenCodeConfig()
            self.save_global_config()

        return self._global_config

    def save_global_config(self) -> None:
        """Save global OpenCode configuration"""
        if self._global_config is None:
            return

        self.ensure_global_config_dir()

        try:
            with open(self.global_config_file, 'w', encoding='utf-8') as f:
                json.dump(self._global_config.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"Failed to save global configuration: {e}")

    def get_project_config_dir(self, project_path: Union[str, Path]) -> Path:
        """Get project configuration directory"""
        return Path(project_path) / ".opencode" / "spec-kit"

    def get_project_config_file(self, project_path: Union[str, Path]) -> Path:
        """Get project configuration file path"""
        return self.get_project_config_dir(project_path) / "config.json"

    def load_project_config(self, project_path: Union[str, Path]) -> ProjectConfiguration:
        """Load project-specific configuration"""
        project_path_str = str(Path(project_path).resolve())

        if project_path_str in self._project_configs:
            return self._project_configs[project_path_str]

        config_file = self.get_project_config_file(project_path)

        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                config = ProjectConfiguration.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                # If config is corrupted, create default
                config = ProjectConfiguration(project_path=project_path_str)
                self.save_project_config(project_path, config)
        else:
            # Create default configuration
            config = ProjectConfiguration(project_path=project_path_str)
            self.save_project_config(project_path, config)

        self._project_configs[project_path_str] = config
        return config

    def save_project_config(self, project_path: Union[str, Path], config: ProjectConfiguration) -> None:
        """Save project-specific configuration"""
        config_dir = self.get_project_config_dir(project_path)
        config_file = self.get_project_config_file(project_path)

        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"Failed to save project configuration: {e}")

    def get_merged_config(self, project_path: Union[str, Path]) -> Dict[str, Any]:
        """Get merged configuration (project overrides global)"""
        global_config = self.load_global_config()
        project_config = self.load_project_config(project_path)

        # Start with global config as base
        merged = {
            "opencode": asdict(global_config),
            "project": asdict(project_config),
        }

        return merged

    def update_global_setting(self, key: str, value: Any) -> None:
        """Update a global configuration setting"""
        config = self.load_global_config()

        if hasattr(config, key):
            setattr(config, key, value)
            config.updated_at = None  # Will be set by post_init
            self.save_global_config()
        else:
            raise ValueError(f"Unknown global configuration key: {key}")

    def update_project_setting(self, project_path: Union[str, Path], key: str, value: Any) -> None:
        """Update a project configuration setting"""
        config = self.load_project_config(project_path)

        if hasattr(config, key):
            setattr(config, key, value)
            config.updated_at = None  # Will be set by post_init
            self.save_project_config(project_path, config)
        else:
            raise ValueError(f"Unknown project configuration key: {key}")

    def get_setting(self, project_path: Union[str, Path], key: str, default: Any = None) -> Any:
        """Get a configuration setting (project overrides global)"""
        # First try project config
        project_config = self.load_project_config(project_path)
        if hasattr(project_config, key):
            value = getattr(project_config, key)
            if value is not None:
                return value

        # Fall back to global config
        global_config = self.load_global_config()
        if hasattr(global_config, key):
            value = getattr(global_config, key)
            if value is not None:
                return value

        return default

    def is_spec_kit_enabled(self, project_path: Union[str, Path]) -> bool:
        """Check if spec-kit is enabled for the project"""
        return self.get_setting(project_path, "spec_kit_enabled", True)

    def get_default_template(self, project_path: Union[str, Path]) -> Optional[str]:
        """Get default template for the project"""
        return self.get_setting(project_path, "default_template")

    def is_auto_commit_enabled(self, project_path: Union[str, Path]) -> bool:
        """Check if auto-commit is enabled"""
        return self.get_setting(project_path, "auto_commit", True)

    def is_git_integration_enabled(self, project_path: Union[str, Path]) -> bool:
        """Check if git integration is enabled"""
        return self.get_setting(project_path, "git_integration", True)

    def is_research_enabled(self, project_path: Union[str, Path]) -> bool:
        """Check if research capabilities are enabled"""
        return self.get_setting(project_path, "research_enabled", True)

    def get_custom_setting(self, project_path: Union[str, Path], key: str, default: Any = None) -> Any:
        """Get a custom configuration setting"""
        project_config = self.load_project_config(project_path)
        return project_config.get_setting(key, default)

    def set_custom_setting(self, project_path: Union[str, Path], key: str, value: Any) -> None:
        """Set a custom configuration setting"""
        project_config = self.load_project_config(project_path)
        project_config.update_setting(key, value)
        self.save_project_config(project_path, project_config)

    def clear_cache(self) -> None:
        """Clear configuration cache"""
        self._global_config = None
        self._project_configs.clear()

    def validate_configuration_data(self, config_data: Dict[str, Any], config_type: str = "global") -> Dict[str, Any]:
        """Validate configuration data against JSON schema"""
        issues = []

        try:
            if config_type == "global":
                schema = self._schema.get("definitions", {}).get("opencodeConfig", self._schema)
            elif config_type == "project":
                schema = self._schema.get("definitions", {}).get("projectConfig", self._schema)
            else:
                schema = self._schema

            jsonschema.validate(instance=config_data, schema=schema)
            valid = True
        except jsonschema.ValidationError as e:
            valid = False
            issues.append(f"Schema validation error: {e.message}")
            if e.absolute_path:
                issues.append(f"Path: {' -> '.join(str(p) for p in e.absolute_path)}")
        except jsonschema.SchemaError as e:
            valid = False
            issues.append(f"Schema error: {e.message}")
        except Exception as e:
            valid = False
            issues.append(f"Validation error: {str(e)}")

        return {
            "valid": valid,
            "issues": issues,
            "config_type": config_type
        }

    def validate_global_config(self) -> Dict[str, Any]:
        """Validate global configuration"""
        if self._global_config is None:
            return {
                "valid": False,
                "issues": ["Global config not loaded"],
                "config_type": "global"
            }

        config_data = self._global_config.to_dict()
        return self.validate_configuration_data(config_data, "global")

    def validate_project_config(self, project_path: Union[str, Path]) -> Dict[str, Any]:
        """Validate project configuration"""
        project_config = self._project_configs.get(str(Path(project_path).resolve()))
        if project_config is None:
            return {
                "valid": False,
                "issues": ["Project config not loaded"],
                "config_type": "project"
            }

        config_data = project_config.to_dict()
        return self.validate_configuration_data(config_data, "project")

    def load_state(self) -> Dict[str, Any]:
        """Load state tracking data"""
        if not self.state_file.exists():
            return self._get_default_state()

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return self._get_default_state()

    def save_state(self, state: Dict[str, Any]) -> None:
        """Save state tracking data"""
        self.ensure_global_config_dir()

        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"Failed to save state: {e}")

    def _get_default_state(self) -> Dict[str, Any]:
        """Get default state structure"""
        return {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "projects": {},
            "global_stats": {
                "total_specs_created": 0,
                "total_plans_created": 0,
                "total_tasks_generated": 0,
                "total_research_items": 0
            }
        }

    def update_project_state(self, project_path: Union[str, Path], key: str, value: Any) -> None:
        """Update state for a specific project"""
        state = self.load_state()
        project_key = str(Path(project_path).resolve())

        if project_key not in state["projects"]:
            state["projects"][project_key] = {}

        state["projects"][project_key][key] = value
        state["last_updated"] = datetime.now().isoformat()

        self.save_state(state)

    def get_project_state(self, project_path: Union[str, Path], key: str, default: Any = None) -> Any:
        """Get state value for a specific project"""
        state = self.load_state()
        project_key = str(Path(project_path).resolve())

        project_state = state["projects"].get(project_key, {})
        return project_state.get(key, default)

    def increment_global_stat(self, stat_name: str, increment: int = 1) -> None:
        """Increment a global statistic"""
        state = self.load_state()

        if stat_name not in state["global_stats"]:
            state["global_stats"][stat_name] = 0

        state["global_stats"][stat_name] += increment
        state["last_updated"] = datetime.now().isoformat()

        self.save_state(state)

    def get_global_stat(self, stat_name: str, default: int = 0) -> int:
        """Get a global statistic value"""
        state = self.load_state()
        return state["global_stats"].get(stat_name, default)

    def validate_configuration(self, project_path: Union[str, Path]) -> Dict[str, Any]:
        """Validate configuration and return validation results"""
        issues = []

        # Validate global config
        global_validation = self.validate_global_config()
        if not global_validation["valid"]:
            issues.extend(global_validation["issues"])

        # Validate project config
        project_validation = self.validate_project_config(project_path)
        if not project_validation["valid"]:
            issues.extend(project_validation["issues"])

        # Check directories exist
        if not self.global_config_dir.exists():
            issues.append("Global config directory does not exist")

        project_config_dir = self.get_project_config_dir(project_path)
        if not project_config_dir.exists():
            issues.append("Project config directory does not exist")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "global_config_loaded": self._global_config is not None,
            "project_config_loaded": str(project_path) in self._project_configs,
            "global_validation": global_validation,
            "project_validation": project_validation
        }