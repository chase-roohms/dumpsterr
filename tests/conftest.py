"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
from dotenv import load_dotenv

# Add src directory to Python path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_files_dir(temp_dir):
    """Create a temporary directory with test files."""
    files_dir = Path(temp_dir) / 'test_files'
    files_dir.mkdir()
    
    # Create some test files
    for i in range(5):
        (files_dir / f'file_{i}.txt').write_text(f'Test file {i}')
    
    return str(files_dir)


@pytest.fixture
def empty_dir(temp_dir):
    """Create an empty temporary directory."""
    empty_path = Path(temp_dir) / 'empty'
    empty_path.mkdir()
    return str(empty_path)


@pytest.fixture
def nested_test_dir(temp_dir):
    """Create nested directory structure with files."""
    base = Path(temp_dir) / 'nested'
    base.mkdir()
    
    # Create nested structure
    (base / 'level1').mkdir()
    (base / 'level1' / 'level2').mkdir()
    
    # Add files at each level
    (base / 'file1.txt').write_text('root level')
    (base / 'level1' / 'file2.txt').write_text('level 1')
    (base / 'level1' / 'level2' / 'file3.txt').write_text('level 2')
    
    return str(base)


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        'libraries': [
            {
                'name': 'Movies',
                'path': '/media/movies',
                'min_files': 10,
                'min_threshold': 85
            },
            {
                'name': 'TV Shows',
                'path': ['/media/shows', '/extra/shows'],
                'min_files': 5,
                'min_threshold': 90
            }
        ],
        'settings': {
            'log_level': 'INFO'
        }
    }


@pytest.fixture
def sample_config_yaml(temp_dir, sample_config):
    """Create a temporary YAML config file."""
    import yaml
    config_path = Path(temp_dir) / 'config.yml'
    with open(config_path, 'w') as f:
        yaml.dump(sample_config, f)
    return str(config_path)


@pytest.fixture
def sample_schema_yaml(temp_dir):
    """Create a sample schema file."""
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
            'settings': {
                'type': 'object',
                'properties': {
                    'log_level': {'type': 'string'}
                }
            }
        },
        'required': ['libraries']
    }
    
    import yaml
    schema_path = Path(temp_dir) / 'schema.yml'
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f)
    return str(schema_path)


@pytest.fixture
def plex_env_vars():
    """
    Load Plex environment variables from .env.test file.
    Tests marked with @pytest.mark.plex will skip if these aren't available.
    """
    env_file = Path(__file__).parent.parent / '.env.test'
    if env_file.exists():
        load_dotenv(env_file)
    
    plex_url = os.getenv('PLEX_URL')
    plex_token = os.getenv('PLEX_TOKEN')
    
    if not plex_url or not plex_token:
        pytest.skip('PLEX_URL and PLEX_TOKEN must be set in .env.test for Plex integration tests')
    
    return {
        'url': plex_url,
        'token': plex_token
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "plex: mark test as requiring actual Plex server connection"
    )
