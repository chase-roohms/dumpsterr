# Custom modules
import filesystem
import config
import plex_client

# Standard libraries
import logging
import dotenv
import os
from pprint import pp

def is_dirs_and_counts_valid(directories_min_files: dict) -> bool:
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

def main(config_data: dict, logger: logging.Logger = logging.getLogger(__name__)):
    # Check if directories all are accessible and have minimum file counts
    # Exit if validation fails
    plex = plex_client.PlexClient(
        base_url = os.getenv('PLEX_URL'),
        token=os.getenv('PLEX_TOKEN')
    )
    sections = plex.get_library_sections()
    logging.debug(f'Plex library sections: {sections}')
    try:
        dirs_counts = {path_info['path']: path_info.get('min_files', 0) 
                      for path_info in config_data.get('libraries', [])}
        if not is_dirs_and_counts_valid(dirs_counts):
            quit()
    except Exception as e:
        logger.error(f'An error occurred during directory validation: {e}')
        quit()
    logger.info('All directories are valid and meet the minimum file counts.')
    logger.info('Proceeding with Plex library trash emptying...')
    for library in config_data.get('libraries', []):
        section_name = library['name']
        section_key = sections.get(section_name)
        if section_key:
            success = plex.empty_section_trash(section_key)
            if success:
                logger.info(f'Successfully emptied trash for section "{section_name}".')
            else:
                logger.error(f'Failed to empty trash for section "{section_name}".')
        else:
            logger.error(f'Section "{section_name}" not found in Plex library sections.')

if __name__ == "__main__":
    # Load environment variables
    dotenv.load_dotenv('data/.env')
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

    main(config_data, logger)
