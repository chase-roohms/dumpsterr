import yaml
import jsonschema
from pprint import pp

def _get_yaml(file_path: str):
    '''
    Load a YAML file and return its contents as a dictionary.
    
    :param file_path: Path to the YAML file
    '''
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data

def _validate_schema(config: dict, schema_path: str = 'src/public/config.schema.json'):
    '''
    Validate the configuration data against the JSON schema.
    
    :param config: Configuration data to validate
    :param schema_path: Path to the JSON schema file
    '''
    schema_data = _get_yaml(schema_path)
    jsonschema.validate(instance=config, schema=schema_data)

def get_config(config_path: str = 'data/config.yml'):
    '''
    Load and validate the configuration file.
    
    :param config_path: Path to the configuration file
    '''
    config = _get_yaml(config_path)
    _validate_schema(config)
    return config

if __name__ == "__main__":
    # Example usage / testing
    config = get_config()
    pp(config)