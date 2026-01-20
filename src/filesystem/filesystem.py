import os
from pathlib import Path

def _validate_directory(path: str) -> None:
    """Ensure that the directory at the given path exists and is readable.
    
    Args:
        path: Path to the directory.
        
    Raises:
        FileNotFoundError: If the directory does not exist.
        NotADirectoryError: If the path is not a directory.
        PermissionError: If read permission is denied.
    """
    dir_path = Path(path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory does not exist: {path}")
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")
    if not os.access(dir_path, os.R_OK):
        raise PermissionError(f"Read permission denied for directory: {path}")

def is_valid_directory(path: str) -> tuple[bool, str]:
    """Check if the directory at the given path exists and is readable.
    
    Args:
        path: Path to the directory.
        
    Returns:
        Tuple of (validity, error_message) where validity is True if valid, 
        False otherwise, and error_message is empty string if valid or the 
        error description if invalid.
    """
    try:
        _validate_directory(path)
        return True, ''
    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        return False, str(e)

def get_file_counts(directory: str) -> int:
    """Get the count of files in the specified directory.
    
    Args:
        directory: Path to the directory.
        
    Returns:
        Number of files in the directory.
    """
    _validate_directory(directory)
    dir_path = Path(directory)
    return len([f for f in dir_path.iterdir()])