import yaml
import jsonschema
from pprint import pp

def _get_yaml(file_path: str) -> dict:
    """Load a YAML file and return its contents as a dictionary.
    
    Args:
        file_path: Path to the YAML file.
        
    Returns:
        Dictionary containing the YAML file contents.
    """
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data

def _validate_schema(config: dict, schema_path: str = 'src/public/config.schema.json') -> None:
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