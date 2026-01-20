import yaml
import jsonschema
import os

def _get_yaml(file_path: str) -> dict:
    """Load a YAML file and return its contents as a dictionary.
    
    Args:
        file_path: Path to the YAML file.
        
    Returns:
        Dictionary containing the YAML file contents.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Configuration file not found: {file_path}\n"
            f"If running in Docker, ensure the config file exists on the host before starting the container."
        )
    
    if os.path.isdir(file_path):
        raise IsADirectoryError(
            f"Expected a file but found a directory: {file_path}\n"
            f"This usually means the config file doesn't exist on the host system.\n"
            f"Docker created a directory instead when mounting the volume.\n"
            f"Solution: Create the config file on your host at the source path specified in your docker-compose.yml,\n"
            f"then recreate the container with 'docker compose down && docker compose up -d'"
        )
    
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data

def _validate_schema(config: dict, schema_path: str = 'schemas/config.schema.yml') -> None:
    """Validate the configuration data against the JSON schema.
    
    Args:
        config: Configuration data to validate.
        schema_path: Path to the JSON schema file.
        
    Raises:
        jsonschema.ValidationError: If the configuration does not conform to the schema.
    """
    schema_data = _get_yaml(schema_path)
    jsonschema.validate(instance=config, schema=schema_data)

def get_config(config_path: str = 'data/config.yml') -> dict:
    """Load and validate the configuration file.
    
    Args:
        config_path: Path to the configuration file.
        
    Returns:
        Dictionary containing the configuration data.
        
    Raises:
        jsonschema.ValidationError: If the configuration does not conform to the schema.
    """
    config = _get_yaml(config_path)
    _validate_schema(config)
    return config

if __name__ == "__main__":
    # Example usage / testing
    config = get_config()
    pp(config)