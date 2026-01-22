import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def _validate_directory(path: str) -> None:
    """Ensure that the directory at the given path exists and is readable.
    
    Follows symlinks and validates that symlink targets exist and are readable.
    
    Args:
        path: Path to the directory.
        
    Raises:
        FileNotFoundError: If the directory does not exist or symlink target is broken.
        NotADirectoryError: If the path is not a directory.
        PermissionError: If read permission is denied.
    """
    dir_path = Path(path)
    
    # Check if path is a symlink and validate its target
    if dir_path.is_symlink():
        # Resolve the symlink to its target (strict=True ensures it exists)
        try:
            resolved_path = dir_path.resolve(strict=True)
        except (OSError, RuntimeError) as e:
            raise FileNotFoundError(f"Broken symlink or circular reference: {path}") from e
        
        # Validate the resolved target is a directory with read permissions
        if not resolved_path.is_dir():
            raise NotADirectoryError(f"Symlink target is not a directory: {path} -> {resolved_path}")
        if not os.access(resolved_path, os.R_OK):
            raise PermissionError(f"Read permission denied for symlink target: {path} -> {resolved_path}")
    else:
        # Standard validation for non-symlink paths
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
    
    Validates symlinks and only counts items that exist and are accessible.
    Broken symlinks are excluded from the count.
    
    Args:
        directory: Path to the directory.
        
    Returns:
        Number of valid files/directories in the directory (excluding broken symlinks).
    """
    _validate_directory(directory)
    dir_path = Path(directory)
    
    count = 0
    for item in dir_path.iterdir():
        # If it's a symlink, verify it resolves to an existing target
        if item.is_symlink():
            try:
                # Check if the symlink target exists
                if item.resolve(strict=True).exists():
                    count += 1
                # If resolve succeeds but target doesn't exist, skip it (broken symlink)
            except (OSError, RuntimeError) as e:
                # Broken symlink or circular reference - skip it
                logger.debug(f"Skipping broken symlink: {item} ({e})")
                pass
        else:
            # Regular file or directory - count it
            count += 1
    
    return count