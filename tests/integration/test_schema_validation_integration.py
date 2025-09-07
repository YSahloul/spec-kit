"""
Test Schema Validation Integration - T049
Tests the integration of spec-kit schema validation with OpenCode
"""

import json
import pytest
from pathlib import Path
from specify_cli.services.opencode_integration import OpenCodeIntegration
from specify_cli.services.configuration_service import ConfigurationService


class TestSchemaValidationIntegration:
    """Test cases for schema validation integration with OpenCode"""

    def test_schema_registration(self):
        """Test that schema is properly registered during initialization"""
        integration = OpenCodeIntegration()

        # Initialize the integration
        result = integration.initialize()

        # Verify initialization was successful
        assert result['status'] == 'success'
        assert integration._schema_registered == True
        assert len(integration._validation_hooks) > 0

    def test_validation_hooks_available(self):
        """Test that validation hooks are properly set up"""
        integration = OpenCodeIntegration()
        integration.initialize()

        # Check that required validation hooks are available
        expected_hooks = ['validate_config', 'validate_project_config', 'get_schema_info']
        available_hooks = list(integration._validation_hooks.keys())

        for hook in expected_hooks:
            assert hook in available_hooks

    def test_plugin_definition_includes_validation(self):
        """Test that plugin definition includes validation information"""
        integration = OpenCodeIntegration()
        integration.initialize()

        plugin = integration.create_opencode_plugin()

        # Check that validation section exists
        assert 'validation' in plugin
        validation_info = plugin['validation']

        assert validation_info['schema_registered'] == True
        assert 'validation_hooks' in validation_info
        assert 'supported_config_types' in validation_info
        assert 'schema_info' in validation_info

    def test_opencode_config_validation(self):
        """Test validation of OpenCode configuration data"""
        integration = OpenCodeIntegration()
        integration.initialize()

        # Valid OpenCode config
        valid_config = {
            "version": "1.0.0",
            "theme": "dark",
            "auto_save": True,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }

        result = integration.validate_opencode_config(valid_config)
        assert result['valid'] == True
        assert len(result['issues']) == 0

        # Invalid OpenCode config (missing required version)
        invalid_config = {
            "theme": "dark",
            "auto_save": True
        }

        result = integration.validate_opencode_config(invalid_config)
        assert result['valid'] == False
        assert len(result['issues']) > 0

    def test_project_config_validation(self):
        """Test validation of project configuration data"""
        integration = OpenCodeIntegration()
        integration.initialize()

        # Create a temporary project directory for testing
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Valid project config
            valid_config = {
                "project_path": str(project_path),
                "spec_kit_enabled": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }

            result = integration.validate_project_config(str(project_path), valid_config)
            assert result['valid'] == True
            assert len(result['issues']) == 0

            # Invalid project config (missing required project_path)
            invalid_config = {
                "spec_kit_enabled": True
            }

            result = integration.validate_project_config(str(project_path), invalid_config)
            assert result['valid'] == False
            assert len(result['issues']) > 0

    def test_schema_information_retrieval(self):
        """Test retrieval of schema information"""
        integration = OpenCodeIntegration()
        integration.initialize()

        schema_info = integration.get_schema_information()

        assert 'schema_version' in schema_info
        assert 'title' in schema_info
        assert 'description' in schema_info
        assert 'definitions' in schema_info
        assert 'supported_config_types' in schema_info

        assert schema_info['title'] == 'OpenCode Spec-Kit Configuration Schema'
        assert 'opencode' in schema_info['supported_config_types']
        assert 'project' in schema_info['supported_config_types']

    def test_validation_status_reporting(self):
        """Test validation status reporting"""
        integration = OpenCodeIntegration()
        integration.initialize()

        status = integration.get_validation_status()

        assert status['schema_registered'] == True
        assert status['validation_hooks_available'] > 0
        assert 'schema_info' in status

    def test_callback_registration(self):
        """Test that validation callbacks can be registered"""
        integration = OpenCodeIntegration()
        integration.initialize()

        # Mock callback registry
        callback_registry = {}

        # Register validation callbacks
        integration.register_validation_callbacks(callback_registry)

        # Verify callbacks were registered
        expected_callbacks = ['validate_config', 'validate_project_config', 'get_schema_info']
        for callback_name in expected_callbacks:
            assert callback_name in callback_registry
            assert callable(callback_registry[callback_name])

    def test_configuration_service_integration(self):
        """Test integration with ConfigurationService validation"""
        config_service = ConfigurationService()
        integration = OpenCodeIntegration(config_service)
        integration.initialize()

        # Test that the integration uses the same schema as ConfigurationService
        integration_schema_info = integration.get_schema_information()
        config_schema = config_service._schema

        assert integration_schema_info['title'] == config_schema['title']
        assert set(integration_schema_info['definitions']) == set(config_schema['definitions'].keys())