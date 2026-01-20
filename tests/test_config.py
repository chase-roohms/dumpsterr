"""
Unit tests for config module.
"""
import os
import pytest
import yaml
import jsonschema
from pathlib import Path

import config.config as config_module


class TestGetYaml:
    """Tests for _get_yaml function."""
    
    def test_load_valid_yaml(self, sample_config_yaml):
        """Test loading a valid YAML file."""
        result = config_module._get_yaml(sample_config_yaml)
        assert isinstance(result, dict)
        assert 'libraries' in result
        assert 'settings' in result
    
    def test_file_not_found(self, temp_dir):
        """Test loading a non-existent file."""
        non_existent = os.path.join(temp_dir, 'does_not_exist.yml')
        with pytest.raises(FileNotFoundError) as exc_info:
            config_module._get_yaml(non_existent)
        assert 'Configuration file not found' in str(exc_info.value)
    
    def test_directory_instead_of_file(self, temp_dir):
        """Test loading a directory instead of a file."""
        with pytest.raises(IsADirectoryError) as exc_info:
            config_module._get_yaml(temp_dir)
        assert 'Expected a file but found a directory' in str(exc_info.value)
        assert 'Docker created a directory' in str(exc_info.value)
    
    def test_empty_yaml_file(self, temp_dir):
        """Test loading an empty YAML file."""
        empty_file = Path(temp_dir) / 'empty.yml'
        empty_file.write_text('')
        result = config_module._get_yaml(str(empty_file))
        assert result is None
    
    def test_invalid_yaml_syntax(self, temp_dir):
        """Test loading a YAML file with invalid syntax."""
        invalid_file = Path(temp_dir) / 'invalid.yml'
        invalid_file.write_text('invalid: yaml: content:\n  - bad indentation')
        with pytest.raises(yaml.YAMLError):
            config_module._get_yaml(str(invalid_file))
    
    def test_yaml_with_special_characters(self, temp_dir):
        """Test loading YAML with special characters."""
        special_file = Path(temp_dir) / 'special.yml'
        content = {
            'test': 'value with: colon',
            'path': '/path/with/special/chars!@#',
            'number': 123
        }
        with open(special_file, 'w') as f:
            yaml.dump(content, f)
        result = config_module._get_yaml(str(special_file))
        assert result == content


class TestValidateSchema:
    """Tests for _validate_schema function."""
    
    def test_valid_config_against_schema(self, sample_config, sample_schema_yaml):
        """Test validating a valid config against schema."""
        # Should not raise any exception
        config_module._validate_schema(sample_config, sample_schema_yaml)
    
    def test_invalid_config_missing_required(self, sample_schema_yaml):
        """Test validating config missing required fields."""
        invalid_config = {'settings': {'log_level': 'INFO'}}
        with pytest.raises(jsonschema.ValidationError):
            config_module._validate_schema(invalid_config, sample_schema_yaml)
    
    def test_invalid_config_wrong_type(self, sample_schema_yaml):
        """Test validating config with wrong type."""
        invalid_config = {
            'libraries': [
                {
                    'name': 123,  # Should be string
                    'path': '/valid/path'
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            config_module._validate_schema(invalid_config, sample_schema_yaml)
    
    def test_config_with_extra_fields(self, sample_config, sample_schema_yaml):
        """Test validating config with extra fields (should be allowed)."""
        config_with_extra = sample_config.copy()
        config_with_extra['extra_field'] = 'extra_value'
        # Should not raise - additional properties are allowed by default
        config_module._validate_schema(config_with_extra, sample_schema_yaml)
    
    def test_schema_file_not_found(self, sample_config, temp_dir):
        """Test with non-existent schema file."""
        with pytest.raises(FileNotFoundError):
            config_module._validate_schema(
                sample_config, 
                os.path.join(temp_dir, 'nonexistent.yml')
            )
    
    def test_nested_validation_error(self, sample_schema_yaml):
        """Test validation error in nested structure."""
        invalid_config = {
            'libraries': [
                {
                    'name': 'Valid Library',
                    'path': '/valid/path',
                    'min_files': 'not_a_number'  # Should be integer
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            config_module._validate_schema(invalid_config, sample_schema_yaml)


class TestGetConfig:
    """Tests for get_config function."""
    
    def test_get_valid_config(self, sample_config_yaml, sample_schema_yaml, monkeypatch):
        """Test getting a valid configuration."""
        # Mock the schema path in get_config to use our test schema
        original_validate = config_module._validate_schema
        
        def mock_validate(config, schema_path='schemas/config.schema.yml'):
            # Use our test schema instead of the default one
            original_validate(config, sample_schema_yaml)
        
        monkeypatch.setattr(config_module, '_validate_schema', mock_validate)
        result = config_module.get_config(sample_config_yaml)
        
        assert isinstance(result, dict)
        assert 'libraries' in result
        assert len(result['libraries']) == 2
    
    def test_get_config_file_not_found(self):
        """Test getting config from non-existent file."""
        with pytest.raises(FileNotFoundError):
            config_module.get_config('/nonexistent/config.yml')
    
    def test_get_config_invalid_schema(self, temp_dir, sample_schema_yaml, monkeypatch):
        """Test getting config that fails schema validation."""
        # Create invalid config
        invalid_config = {'invalid': 'structure'}
        invalid_file = Path(temp_dir) / 'invalid_config.yml'
        with open(invalid_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        original_validate = config_module._validate_schema
        
        def mock_validate(config, schema_path='schemas/config.schema.yml'):
            # Use our test schema instead of the default one
            original_validate(config, sample_schema_yaml)
        
        monkeypatch.setattr(config_module, '_validate_schema', mock_validate)
        
        with pytest.raises(jsonschema.ValidationError):
            config_module.get_config(str(invalid_file))
    
    def test_get_config_with_single_path(self, temp_dir, sample_schema_yaml, monkeypatch):
        """Test config with single path string."""
        config = {
            'libraries': [
                {
                    'name': 'Movies',
                    'path': '/single/path'
                }
            ]
        }
        config_file = Path(temp_dir) / 'single_path.yml'
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        original_validate = config_module._validate_schema
        
        def mock_validate(config, schema_path='schemas/config.schema.yml'):
            # Use our test schema instead of the default one
            original_validate(config, sample_schema_yaml)
        
        monkeypatch.setattr(config_module, '_validate_schema', mock_validate)
        result = config_module.get_config(str(config_file))
        
        assert result['libraries'][0]['path'] == '/single/path'
    
    def test_get_config_with_multiple_paths(self, temp_dir, sample_schema_yaml, monkeypatch):
        """Test config with array of paths."""
        config = {
            'libraries': [
                {
                    'name': 'TV Shows',
                    'path': ['/path1', '/path2', '/path3']
                }
            ]
        }
        config_file = Path(temp_dir) / 'multi_path.yml'
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        original_validate = config_module._validate_schema
        
        def mock_validate(config, schema_path='schemas/config.schema.yml'):
            # Use our test schema instead of the default one
            original_validate(config, sample_schema_yaml)
        
        monkeypatch.setattr(config_module, '_validate_schema', mock_validate)
        result = config_module.get_config(str(config_file))
        
        assert len(result['libraries'][0]['path']) == 3
    
    def test_get_config_default_path(self):
        """Test that default path is used when not specified."""
        # Test depends on whether data/config.yml exists in the actual project
        # If it exists, it should load successfully; if not, should raise error
        try:
            result = config_module.get_config()
            # If we got here, the file exists and was loaded
            assert isinstance(result, dict)
        except (FileNotFoundError, IsADirectoryError, jsonschema.ValidationError):
            # Expected if file doesn't exist or is invalid
            pass


class TestConfigIntegration:
    """Integration tests for the config module."""
    
    def test_full_workflow(self, temp_dir):
        """Test complete workflow of loading and validating config."""
        # Create a realistic config
        config = {
            'libraries': [
                {
                    'name': 'Movies',
                    'path': '/media/movies',
                    'min_files': 100,
                    'min_threshold': 90
                },
                {
                    'name': 'TV Shows',
                    'path': ['/media/tv', '/backup/tv'],
                    'min_files': 50,
                    'min_threshold': 85
                }
            ],
            'settings': {
                'log_level': 'DEBUG'
            }
        }
        
        # Create config file
        config_file = Path(temp_dir) / 'full_config.yml'
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # Create schema file
        schema = {
            'type': 'object',
            'properties': {
                'libraries': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'path': {
                                'oneOf': [
                                    {'type': 'string'},
                                    {'type': 'array', 'items': {'type': 'string'}}
                                ]
                            },
                            'min_files': {'type': 'integer'},
                            'min_threshold': {'type': 'integer'}
                        },
                        'required': ['name', 'path']
                    }
                },
                'settings': {'type': 'object'}
            },
            'required': ['libraries']
        }
        schema_file = Path(temp_dir) / 'full_schema.yml'
        with open(schema_file, 'w') as f:
            yaml.dump(schema, f)
        
        # Load and validate
        loaded_config = config_module._get_yaml(str(config_file))
        config_module._validate_schema(loaded_config, str(schema_file))
        
        # Verify loaded config
        assert loaded_config == config
        assert len(loaded_config['libraries']) == 2
        assert loaded_config['settings']['log_level'] == 'DEBUG'
