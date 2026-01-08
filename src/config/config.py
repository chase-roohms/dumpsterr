import yaml
import jsonschema
from pprint import pp

def get_config(config_path='data/config.yml'):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    validate_schema(config)
    return config

def validate_schema(config, schema_path='src/config/config.schema.json'):
    with open(schema_path, 'r') as file:
        schema_data = yaml.safe_load(file)
    jsonschema.validate(instance=config, schema=schema_data)

if __name__ == "__main__":
    # Example usage / testing
    config = get_config()
    pp(config)