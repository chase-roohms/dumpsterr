# Standard libraries
import logging
import os
import sys
from typing import Optional

# Third-party libraries
import jsonschema

# Custom modules
import config
import filesystem
import plex_client

DEFAULT_MIN_FILES = 0
DEFAULT_MIN_THRESHOLD = 90


def is_dirs_valid(directories: list[str]) -> bool:
    """Check the validity of directories as specified in the configuration data.
    
    Verify each directory exists and is readable.
    
    Args:
        directories: List of directory paths to validate.
        
    Returns:
        True if all directories are valid and accessible, False otherwise.
    """
    for path in directories:
        is_valid_dir, error = filesystem.is_valid_directory(path)
        if not is_valid_dir:
            logging.error(f'Directory "{path}" is invalid or inaccessible: {error}')
            return False
        logging.info(f'Directory "{path}" is valid and accessible.')
    return True


def is_dirs_counts_valid(directories_min_files: dict[str, int]) -> bool:
    """Check the validity of directories and file counts.
    
    Verify each directory exists and is readable. Check if the number of files 
    in each directory meets the minimum expected count.
    
    Args:
        directories_min_files: Mapping of directory paths to their expected 
            minimum file counts.
            
    Returns:
        True if all directories are valid and meet file count requirements, 
        False otherwise.
    """
    for path, min_count in directories_min_files.items():
        is_valid_dir, error = filesystem.is_valid_directory(path)
        if not is_valid_dir:
            logging.error(f'Directory "{path}" is invalid or inaccessible: {error}')
            return False
        count = filesystem.get_file_counts(path)
        logging.debug(f'Number of files in "{path}": {count}')
        if count < min_count:
            logging.warning(f'File count {count} is below the minimum expected {min_count} for path "{path}".')
            return False
        logging.info(f'Directory "{path}" meets the minimum file count of {min_count}.')
    return True


def is_dirs_thresholds_valid(
    directories_min_thresholds: dict[str, float], 
    path_expected_media_counts: dict[str, int]
) -> bool:
    """Check the validity of directories and file count thresholds.
    
    Verify each directory exists and is readable. Check if the percentage of 
    files in each directory meets the minimum threshold.
    
    Args:
        directories_min_thresholds: Mapping of directory paths to their expected 
            file count thresholds (as percentages).
        path_expected_media_counts: Mapping of directory paths to their expected 
            media counts from Plex.
            
    Returns:
        True if all directories are valid and meet threshold requirements, 
        False otherwise.
    """
    for path, threshold in directories_min_thresholds.items():
        is_valid_dir, error = filesystem.is_valid_directory(path)
        if not is_valid_dir:
            logging.error(f'Directory "{path}" is invalid or inaccessible: {error}')
            return False
        count = filesystem.get_file_counts(path)
        logging.debug(f'Number of files in "{path}": {count}')
        media_count = path_expected_media_counts[path]
        logging.debug(f'Plex media count for "{path}": {media_count}')
        # Calculate the actual percentage based on criteria
        actual_percentage = (count / media_count * 100) if media_count > 0 else 0
        logging.debug(f'File count percentage for "{path}": {actual_percentage}%')
        if actual_percentage < threshold:
            logging.warning(f'File count percentage {actual_percentage}% is below the minimum expected {threshold}% for path "{path}".')
            return False
        logging.info(f'Directory "{path}" meets the minimum file count threshold of {threshold}%.')
    return True


def main(config_data: dict, logger: Optional[logging.Logger] = None) -> None:
    """Main function to validate directories and empty Plex trash.
    
    Args:
        config_data: Configuration dictionary loaded from config file.
        logger: Logger instance for logging messages. If None, uses root logger.
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    # Check if directories all are accessible and have minimum file counts
    # Exit if validation fails
    plex = plex_client.PlexClient(
        base_url = os.getenv('PLEX_URL'),
        token=os.getenv('PLEX_TOKEN')
    )
    # Set up Plex client and retrieve library sections / media counts
    sections = plex.get_library_sections()
    logging.debug(f'Plex library sections: {sections}')
    section_media_counts = dict()
    path_media_counts = dict()
    for section, key in sections.items():
        media_count = plex.get_library_size(key)
        section_media_counts[section] = media_count
        logger.info(f'Plex Section: {section}, Size: {media_count}')
    for library in config_data.get('libraries', []):
        section_name = library['name']
        path = library['path']
        media_count = section_media_counts.get(section_name, 0)
        path_media_counts[path] = media_count
    logger.debug(f'Path to media counts: {path_media_counts}')

    # Build directory validation dictionaries in a single iteration
    dirs_counts = {}
    dirs_thresholds = {}
    for path_info in config_data.get('libraries', []):
        path = path_info['path']
        dirs_counts[path] = path_info.get('min_files', DEFAULT_MIN_FILES)
        dirs_thresholds[path] = path_info.get('min_threshold', DEFAULT_MIN_THRESHOLD)
    
    if not is_dirs_valid(list(dirs_counts.keys())):
        logger.error('Directory validation failed. Exiting.')
        sys.exit(1)
    if not is_dirs_counts_valid(dirs_counts):
        logger.error('Directory file count validation failed. Exiting.')
        sys.exit(1)
    if not is_dirs_thresholds_valid(dirs_thresholds, path_media_counts):
        logger.error('Directory file count threshold validation failed. Exiting.')
        sys.exit(1)
    
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
    # Load configuration
    try:
        config_data = config.get_config()
    except (jsonschema.ValidationError, FileNotFoundError, PermissionError) as e:
        print(f'Failed to load configuration: {e}')
        sys.exit(1)
    
    # Configure logging
    log_level = config_data.get('settings', {}).get('log_level', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.debug(f'Configuration loaded: {config_data}')

    main(config_data, logger)
