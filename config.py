import yaml
from pprint import pp

def get_config(config_path='config.yml'):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

if __name__ == "__main__":
    # Example usage / testing
    config = get_config()
    pp(config)