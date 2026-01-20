# Testing Documentation

This directory contains comprehensive tests for the dumpsterr project.

## Setup

Install testing dependencies:

```bash
pip install -r requirements.txt
# Or for development with separate requirements:
pip install -r requirements-dev.txt
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage report
```bash
pytest --cov=src --cov-report=html
```

### Run specific test files
```bash
pytest tests/test_config.py
pytest tests/test_filesystem.py
pytest tests/test_plex_client.py
pytest tests/test_main.py
```

### Run tests by marker
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip Plex integration tests (require real server)
pytest -m "not plex"
```

### Run specific test classes or methods
```bash
pytest tests/test_config.py::TestGetConfig
pytest tests/test_filesystem.py::TestIsValidDirectory::test_valid_directory_returns_true
```

### Run with verbose output
```bash
pytest -v
pytest -vv  # Extra verbose
```

## Test Organization

### test_config.py
- Tests for configuration loading and validation
- YAML parsing
- JSON schema validation
- Configuration file error handling

### test_filesystem.py
- Directory validation tests
- File counting functionality
- Permission handling
- Edge cases (symlinks, special characters, unicode)

### test_plex_client.py
- PlexClient initialization
- API endpoint mocking with `responses` library
- HTTP error handling
- Retry logic
- **Real Plex integration tests** (marked with `@pytest.mark.plex`)

### test_main.py
- Main function integration tests
- Library processing workflow
- Configuration to execution pipeline
- Mock Plex client interactions
- Exit code validation

## Plex Integration Tests

Some tests require a real Plex server connection. These are marked with `@pytest.mark.plex` and will be skipped unless you configure them.

### Setup for Plex Integration Tests

1. Copy the example environment file:
   ```bash
   cp .env.test.example .env.test
   ```

2. Edit `.env.test` with your actual Plex server details:
   ```
   PLEX_URL=http://your-plex-server:32400
   PLEX_TOKEN=your_actual_plex_token
   ```

3. Run Plex integration tests:
   ```bash
   pytest -m plex
   ```

To skip Plex integration tests:
```bash
pytest -m "not plex"
```

## Test Coverage

Generate HTML coverage report:
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

View coverage in terminal:
```bash
pytest --cov=src --cov-report=term-missing
```

## Fixtures

Common fixtures are defined in `conftest.py`:

- `temp_dir`: Temporary directory for test files
- `test_files_dir`: Directory with sample test files
- `empty_dir`: Empty directory
- `nested_test_dir`: Nested directory structure
- `sample_config`: Sample configuration dictionary
- `sample_config_yaml`: Temporary YAML config file
- `sample_schema_yaml`: Temporary schema file
- `plex_env_vars`: Plex environment variables for integration tests

## Continuous Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=src --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Writing New Tests

### Test Structure
```python
class TestFeatureName:
    """Tests for specific feature."""
    
    def test_normal_case(self):
        """Test description."""
        # Arrange
        # Act
        # Assert
    
    def test_edge_case(self):
        """Test edge case."""
        pass
    
    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ExpectedException):
            # code that should raise
```

### Using Fixtures
```python
def test_with_fixture(test_files_dir):
    """Use fixture for test."""
    # test_files_dir is automatically created and cleaned up
    assert os.path.exists(test_files_dir)
```

### Mocking External Services
```python
@responses.activate
def test_api_call():
    responses.add(
        responses.GET,
        'http://api.example.com/endpoint',
        json={'data': 'value'},
        status=200
    )
    # Test code that makes the HTTP request
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Descriptive Names**: Test names should describe what they test
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mock External Dependencies**: Use mocks for external services
5. **Test Edge Cases**: Don't just test happy paths
6. **Clean Up**: Use fixtures for setup/teardown
7. **Fast Tests**: Keep tests fast by using mocks
8. **Clear Assertions**: Use specific assertion messages

## Troubleshooting

### Tests fail with import errors
```bash
# Make sure src is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Permission errors on cleanup
- Some tests may fail to clean up temp files due to permissions
- This is handled gracefully with `ignore_errors=True` in fixtures

### Plex integration tests always skip
- Check that `.env.test` file exists and contains valid credentials
- Verify Plex server is accessible from test environment

## Contributing

When adding new features:
1. Write tests first (TDD approach recommended)
2. Ensure all existing tests pass
3. Aim for >80% code coverage
4. Add integration tests for complex workflows
5. Document any special test setup requirements
