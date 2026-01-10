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

def sum_path_file_counts(paths: list[str]) -> int:
    """Sum the file counts across multiple directories.
    
    Args:
        paths: List of directory paths.
        
    Returns:
        Total number of files across all specified directories.
    """
    total_count = 0
    for path in paths:
        is_valid_dir, error = filesystem.is_valid_directory(path)
        if not is_valid_dir:
            raise ValueError(f'Directory "{path}" is invalid or inaccessible: {error}')
        count = filesystem.get_file_counts(path)
        logging.debug(f'Number of files in "{path}": {count}')
        total_count += count
    return total_count

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


def get_section_media_counts(plex: plex_client.PlexClient, sections: dict[str, str]) -> dict[str, int]:
    """Get media counts for each Plex section.
    
    Args:
        plex: PlexClient instance.
        sections: Mapping of section names to their keys.
    Returns:
        Mapping of section names to their media counts.
    """
    section_media_counts = dict()
    # ex: Section: Movies, Key: 1, Media Count: 1200
    for section, key in sections.items():
        media_count = plex.get_library_size(key)
        section_media_counts[section] = media_count
        logging.info(f'Plex Section: {section}, Size: {media_count}')
    return section_media_counts


def get_section_file_counts(all_media_info: list[dict]) -> dict[str, int]:
    """Get file counts for each Plex section based on configured library paths.
    
    Args:
        all_media_info: List of dictionaries containing media information for each section.
    Returns:
        Mapping of section names to their file counts.
    """
    section_file_counts = dict()
    for library in all_media_info:
        section_name = library['name']
        paths = library['path']
        if isinstance(paths, str):
            paths = [paths]
        for path in paths:
            is_valid_dir, error = filesystem.is_valid_directory(path)
            if not is_valid_dir:
                raise ValueError(f'Directory "{path}" is invalid or inaccessible: {error}')
        file_counts = sum_path_file_counts(paths)
        section_file_counts[section_name] = file_counts
    return section_file_counts


def main(config_data: dict, logger: Optional[logging.Logger] = None) -> None:
    """Main function to validate directories and empty Plex trash.
    
    Args:
        config_data: Configuration dictionary loaded from config file.
        logger: Logger instance for logging messages. If None, uses root logger.
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    # Store libraries info for logic checks and persistent storage of data
    # during the run
    all_media_info = list(config_data.get('libraries', []))
    for library in all_media_info:
        if isinstance(library['path'], str):
            library['path'] = [library['path']]
    # Check if directories all are accessible and have minimum file counts
    # Exit if validation fails
    plex = plex_client.PlexClient(
        base_url = os.getenv('PLEX_URL'),
        token=os.getenv('PLEX_TOKEN')
    )
    # Set up Plex client and retrieve library sections
    sections = plex.get_library_sections()
    logging.debug(f'Plex library sections: {sections}')

    # Get media counts for each Plex section
    section_media_counts = get_section_media_counts(plex, sections)

    # Get file counts for each configured library path or path array
    section_file_counts = get_section_file_counts(all_media_info)
    
    # Combine section file counts and media counts into all_media_info
    for library in all_media_info:
        library['file_count'] = section_file_counts.get(library['name'], 0)
        library['media_count'] = section_media_counts.get(library['name'], 0)
    logging.debug(f'All media info with counts: {all_media_info}')

    # Validate each library's directories, minimum file counts, and thresholds
    for library in all_media_info:
        # All valid directories and are accessible
        if not is_dirs_valid(library['path']):
            logger.error(f'One or more directories for library "{library["name"]}" are invalid or inaccessible.')
            sys.exit(1)
        # Minimum file counts
        if library.get('file_count', -1) < library.get('min_files', DEFAULT_MIN_FILES):
            logger.error(f'File counts for library "{library["name"]}" do not meet the minimum required of {library.get("min_files", DEFAULT_MIN_FILES)}.')
            sys.exit(1)
        # Minimum file count thresholds
        expected_media_count = library.get('media_count', 0)
        actual_file_count = library.get('file_count', 0)
        min_threshold = library.get('min_threshold', DEFAULT_MIN_THRESHOLD)
        actual_percentage = (actual_file_count / expected_media_count * 100) if expected_media_count > 0 else 0
        if actual_percentage < min_threshold:
            logger.error(f'File count thresholds for library "{library["name"]}" are not met (minimum {min_threshold}%).')
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
    except (jsonschema.ValidationError, FileNotFoundError, PermissionError, IsADirectoryError) as e:
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
