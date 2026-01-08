import os
from pathlib import Path

def validate_directory(path: str):
    '''
    Ensure that the directory at the given path exists, and that we have at least
    read permission.
    
    :param path: Path to the directory
    '''
    dir_path = Path(path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory does not exist: {path}")
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")
    if not os.access(dir_path, os.R_OK):
        raise PermissionError(f"Read permission denied for directory: {path}")