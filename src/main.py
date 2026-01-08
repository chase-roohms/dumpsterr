# Custom modules
import filesystem
import config

# Standard libraries
import logging
from pprint import pp

def is_dirs_and_counts_valid(directories_min_files: dict):
    '''
    Check the validity of directories and the file counts in directories as 
    specified in the configuration data.
    - Verify each directory exists and is readable.
    - Check if the number of files in each directory meets the minimum expected 
    count.
    
    :param directories_min_files: Mapping of directory paths to their expected 
    file counts
    '''
    for path, min_count in directories_min_files.items():
        is_valid_dir, error = filesystem.is_valid_directory(path)
        if not is_valid_dir:
            logging.error(f'Directory "{path}" is invalid or inaccessible: {error}')
            return False
        count = filesystem.get_file_counts(path)
        logging.info(f'Number of files in "{path}": {count}')
        if count < min_count:
            logging.warning(f'File count {count} is below the minimum expected {min_count} for path "{path}".')
            return False
    return True

if __name__ == "__main__":
    # Load configuration
    try:
        config_data = config.get_config()
    except Exception as e:
        print(f'Failed to load configuration: {e}')
        quit()
    
    # Configure logging
    log_level = config_data.get('settings', {}).get('log_level', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.debug(f'Configuration loaded: {config_data}')

    # Check if directories all are accessible and have minimum file counts
    # Exit if validation fails
    try:
        if not is_dirs_and_counts_valid(config_data.get('directories-min-files', {})):
            quit()
    except Exception as e:
        logger.error(f'An error occurred during directory validation: {e}')
        quit()
    logger.info('All directories are valid and meet the minimum file counts.')
