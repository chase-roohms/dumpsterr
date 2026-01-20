"""Test helper utilities."""
import tempfile
import shutil
from pathlib import Path
from typing import Optional


def create_temp_config(config_dict: dict, schema_dict: Optional[dict] = None):
    """
    Create temporary config and schema files for testing.
    
    Args:
        config_dict: Configuration dictionary to write to YAML
        schema_dict: Optional schema dictionary to write to YAML
        
    Returns:
        tuple: (config_path, schema_path, temp_dir)
    """
    import yaml
    
    temp_dir = tempfile.mkdtemp()
    
    # Write config
    config_path = Path(temp_dir) / 'config.yml'
    with open(config_path, 'w') as f:
        yaml.dump(config_dict, f)
    
    schema_path = None
    if schema_dict:
        schema_path = Path(temp_dir) / 'schema.yml'
        with open(schema_path, 'w') as f:
            yaml.dump(schema_dict, f)
    
    return str(config_path), str(schema_path) if schema_path else None, temp_dir


def create_test_directory_structure(base_path: str, structure: dict):
    """
    Create a directory structure from a dictionary.
    
    Args:
        base_path: Base directory path
        structure: Dictionary defining structure, e.g.:
            {
                'dir1': {
                    'file1.txt': 'content',
                    'subdir': {
                        'file2.txt': 'more content'
                    }
                },
                'file3.txt': 'root content'
            }
    """
    base = Path(base_path)
    
    def _create_structure(current_path: Path, struct: dict):
        for name, content in struct.items():
            item_path = current_path / name
            if isinstance(content, dict):
                # It's a directory
                item_path.mkdir(exist_ok=True)
                _create_structure(item_path, content)
            else:
                # It's a file
                item_path.write_text(str(content))
    
    _create_structure(base, structure)


def mock_plex_responses(sections: dict, sizes: dict, trash_results: dict):
    """
    Create a mock Plex client with predefined responses.
    
    Args:
        sections: Dict of section name to key mappings
        sizes: Dict of section key to size mappings
        trash_results: Dict of section key to trash empty result (bool)
        
    Returns:
        Mock PlexClient instance
    """
    from unittest.mock import Mock
    
    mock_plex = Mock()
    mock_plex.get_library_sections.return_value = sections
    mock_plex.get_library_size.side_effect = lambda key: sizes.get(key, 0)
    mock_plex.empty_section_trash.side_effect = lambda key: trash_results.get(key, False)
    
    return mock_plex


def assert_file_exists(path: str, message: str = ""):
    """Assert that a file exists."""
    assert Path(path).exists(), message or f"File does not exist: {path}"


def assert_directory_exists(path: str, message: str = ""):
    """Assert that a directory exists."""
    p = Path(path)
    assert p.exists() and p.is_dir(), message or f"Directory does not exist: {path}"


def get_file_count_recursive(directory: str) -> int:
    """Get total count of files recursively in directory."""
    total = 0
    for item in Path(directory).rglob('*'):
        if item.is_file():
            total += 1
    return total
