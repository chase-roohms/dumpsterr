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
from observability import setup_logging, MetricsCollector

DEFAULT_MIN_FILES = 0
DEFAULT_MIN_THRESHOLD = 90

def sum_path_file_counts(paths: list[str], logger: logging.Logger) -> int:
    """Sum the file counts across multiple directories.
    
    Args:
        paths: List of directory paths.
        logger: Logger instance for logging messages.
        
    Returns:
        Total number of files across all specified directories.
    """
    total_count = 0
    for path in paths:
        is_valid_dir, error = filesystem.is_valid_directory(path)
        if not is_valid_dir:
            raise ValueError(f'Directory "{path}" is invalid or inaccessible: {error}')
        count = filesystem.get_file_counts(path)
        logger.debug(f'Number of files in "{path}": {count}')
        total_count += count
    return total_count

def is_dirs_valid(directories: list[str], logger: logging.Logger) -> bool:
    """Check the validity of directories as specified in the configuration data.
    
    Verify each directory exists and is readable.
    
    Args:
        directories: List of directory paths to validate.
        logger: Logger instance for logging messages.
        
    Returns:
        True if all directories are valid and accessible, False otherwise.
    """
    for path in directories:
        is_valid_dir, error = filesystem.is_valid_directory(path)
        if not is_valid_dir:
            logger.error(f'Directory "{path}" is invalid or inaccessible: {error}')
            return False
        logger.debug(f'Directory "{path}" is valid and accessible.')
    return True


def get_section_media_counts(plex: plex_client.PlexClient, sections: dict[str, str], logger: logging.Logger) -> dict[str, int]:
    """Get media counts for each Plex section.
    
    Args:
        plex: PlexClient instance.
        sections: Mapping of section names to their keys.
        logger: Logger instance for logging messages.
    Returns:
        Mapping of section names to their media counts.
    """
    section_media_counts = dict()
    # ex: Section: Movies, Key: 1, Media Count: 1200
    for section, key in sections.items():
        media_count = plex.get_library_size(key)
        section_media_counts[section] = media_count
        logger.info(f'Plex Section: {section}, Size: {media_count}')
    return section_media_counts


def get_section_file_counts(all_media_info: list[dict], logger: logging.Logger) -> dict[str, int]:
    """Get file counts for each Plex section based on configured library paths.
    
    Args:
        all_media_info: List of dictionaries containing media information for each section.
        logger: Logger instance for logging messages.
    Returns:
        Mapping of section names to their file counts.
    """
    section_file_counts = dict()
    for library in all_media_info:
        section_name = library['name']
        paths = library['path']
        if isinstance(paths, str):
            paths = [paths]
        # Validation will be done later in process_library via is_dirs_valid
        file_counts = sum_path_file_counts(paths, logger)
        section_file_counts[section_name] = file_counts
    return section_file_counts

def process_library(plex: plex_client.PlexClient, library: dict, logger: logging.Logger) -> bool:
    """Process a single library: validate and empty trash if checks pass.
    
    Args:
        plex: PlexClient instance.
        library: Library configuration dictionary.
        logger: Logger instance.
        
    Returns:
        True if successful, False otherwise.
    """
    # All valid directories and are accessible
    if not is_dirs_valid(library['path'], logger):
        logger.error(f'One or more directories for library "{library["name"]}" are invalid or inaccessible.')
        return False
    logger.info(f'All directories for library "{library["name"]}" are valid and accessible.')
    # Minimum file counts
    if library.get('file_count', -1) < library.get('min_files', DEFAULT_MIN_FILES):
        logger.error(f'File counts for library "{library["name"]}" are not met (actual {library.get("file_count", -1)}, minimum {library.get("min_files", DEFAULT_MIN_FILES)}).')
        return False
    logger.info(f'File counts for library "{library["name"]}" are met (actual {library.get("file_count", -1)}, minimum {library.get("min_files", DEFAULT_MIN_FILES)}).')
    # Minimum file count thresholds
    expected_media_count = library.get('media_count', 0)
    actual_file_count = library.get('file_count', 0)
    min_threshold = library.get('min_threshold', DEFAULT_MIN_THRESHOLD)
    actual_percentage = (actual_file_count / expected_media_count * 100) if expected_media_count > 0 else 0
    if actual_percentage < min_threshold:
        logger.error(f'File count thresholds for library "{library["name"]}" are not met (actual {actual_percentage:.2f}%, minimum {min_threshold}%).')
        return False
    logger.info(f'File count thresholds for library "{library["name"]}" are met (actual {actual_percentage:.2f}%, minimum {min_threshold}%).')
    logger.info(f'All validation checks passed for library "{library["name"]}". Emptying trash...')
    section_name = library['name']
    section_key = library['section_key']
    if section_key:
        success = plex.empty_section_trash(section_key)
        if success:
            logger.info(f'Successfully emptied trash for section "{section_name}".')
        else:
            logger.error(f'Failed to empty trash for section "{section_name}".')
            return False
    else:
        logger.error(f'Section "{section_name}" not found in Plex library sections.')
        return False
    return True # Successfully processed library


def main(config_data: dict, logger: Optional[logging.Logger] = None, metrics_collector: Optional[MetricsCollector] = None) -> int:
    """Main function to validate directories and empty Plex trash.
    
    Args:
        config_data: Configuration dictionary loaded from config file.
        logger: Logger instance for logging messages. If None, uses root logger.
        metrics_collector: Optional metrics collector for observability.
        
    Returns:
        Exit code: 0 for success, 1 for partial failures, 2 for complete failure.
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    if metrics_collector:
        metrics_collector.start_run()
    
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
    logger.debug(f'Plex library sections: {sections}')

    # Get media counts for each Plex section
    section_media_counts = get_section_media_counts(plex, sections, logger)

    # Get file counts for each configured library path or path array
    section_file_counts = get_section_file_counts(all_media_info, logger)
    
    # Combine section file counts and media counts into all_media_info
    failed_libraries = []
    successful_libraries = []
    
    for library in all_media_info:
        library['file_count'] = section_file_counts.get(library['name'], 0)
        library['media_count'] = section_media_counts.get(library['name'], 0)
        library['section_key'] = sections.get(library['name'])
        
        # Calculate actual percentage for metrics
        expected_media_count = library['media_count']
        actual_file_count = library['file_count']
        actual_percentage = (actual_file_count / expected_media_count * 100) if expected_media_count > 0 else 0
        
        success = process_library(plex, library, logger)
        
        if success:
            logger.info(f'Library "{library["name"]}" processed successfully.')
            successful_libraries.append(library['name'])
        else:
            logger.error(f'Library "{library["name"]}" processing failed.')
            failed_libraries.append(library['name'])
        
        # Record metrics if collector is provided
        if metrics_collector:
            metrics_collector.add_library_result(
                name=library['name'],
                success=success,
                file_count=actual_file_count,
                media_count=expected_media_count,
                threshold_percentage=actual_percentage,
                error_message=None if success else "Validation or trash emptying failed"
            )
    
    # Report final status
    total_libraries = len(all_media_info)
    exit_code = 0
    
    if failed_libraries:
        logger.error(f'Processing completed with errors. Failed: {len(failed_libraries)}/{total_libraries} libraries: {", ".join(failed_libraries)}')
        if successful_libraries:
            logger.info(f'Successfully processed: {", ".join(successful_libraries)}')
            exit_code = 1  # Partial failure
        else:
            exit_code = 2  # Complete failure
    else:
        logger.info(f'All {total_libraries} libraries processed successfully.')
        exit_code = 0  # Success
    
    # Finalize metrics
    if metrics_collector:
        metrics_collector.end_run(exit_code)
        metrics_collector.save_metrics()
        # Metrics saving is now optional with graceful failure handling
    
    return exit_code


if __name__ == "__main__":
    # Load configuration
    try:
        config_data = config.get_config()
    except (jsonschema.ValidationError, FileNotFoundError, PermissionError, IsADirectoryError) as e:
        print(f'Failed to load configuration: {e}')
        sys.exit(1)
    
    # Configure logging with optional JSON format and file rotation
    log_level = config_data.get('settings', {}).get('log_level', 'INFO')
    log_format = os.getenv('LOG_FORMAT', 'standard')  # 'standard' or 'json'
    log_file = os.getenv('LOG_FILE')  # Optional file path for rotation
    
    logger = setup_logging(
        log_level=log_level,
        log_format=log_format,
        log_file=log_file
    )
    logger.debug(f'Configuration loaded: {config_data}')
    
    # Initialize metrics collector
    metrics_collector = MetricsCollector()

    exit_code = main(config_data, logger, metrics_collector)
    sys.exit(exit_code)
