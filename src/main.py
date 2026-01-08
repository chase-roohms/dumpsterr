# Custom modules
import filesystem
import config

# Standard libraries
import logging
from pprint import pp


if __name__ == "__main__":
    config_data = config.get_config()
    
    # Configure logging
    log_level = config_data.get('settings', {}).get('log_level', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.debug(f'Configuration loaded: {config_data}')
