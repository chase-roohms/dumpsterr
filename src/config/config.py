import yaml
import jsonschema
from pprint import pp

def get_yaml(file_path: str):
    '''
    Load a YAML file and return its contents as a dictionary.
    
    :param file_path: Path to the YAML file
    '''
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data

def get_config(config_path: str = 'data/config.yml'):
    '''
    Load and validate the configuration file.
    
    :param config_path: Path to the configuration file
    '''
    config = get_yaml(config_path)
    validate_schema(config)
    return config

def validate_schema(config: dict, schema_path: str = 'src/config/config.schema.json'):
    '''
    Validate the configuration data against the JSON schema.
    
    :param config: Configuration data to validate
    :param schema_path: Path to the JSON schema file
    '''
    schema_data = get_yaml(schema_path)
    jsonschema.validate(instance=config, schema=schema_data)

if __name__ == "__main__":
    # Example usage / testing
    config = get_config()
    pp(config)