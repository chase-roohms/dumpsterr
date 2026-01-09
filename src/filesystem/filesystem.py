import os
from pathlib import Path

def _validate_directory(path: str) -> None:
    '''
    Ensure that the directory at the given path exists, and that we have at least
    read permission.
    
    :param path: Path to the directory
    :raises FileNotFoundError: If the directory does not exist
    :raises NotADirectoryError: If the path is not a directory
    :raises PermissionError: If read permission is denied
    '''
    dir_path = Path(path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory does not exist: {path}")
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")
    if not os.access(dir_path, os.R_OK):
        raise PermissionError(f"Read permission denied for directory: {path}")

def is_valid_directory(path: str) -> tuple[bool, str]:
    '''
    Check if the directory at the given path exists and is readable.
    
    :param path: Path to the directory
    :return validity, error_message: Tuple of (validity, error_message) where 
        validity is True if valid, False otherwise, and error_message is empty 
        string if valid or the error description if invalid
    '''
    try:
        _validate_directory(path)
        return True, ''
    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        return False, str(e)

def get_file_counts(directory: str) -> int:
    '''
    Get the count of files in the specified directory.
    
    :param directory: Path to the directory
    :return count: Number of files in the directory
    '''
    _validate_directory(directory)
    dir_path = Path(directory)
    return len([f for f in dir_path.iterdir()])

if __name__ == "__main__":
    # Example usage / testing
    test_dir = 'data'
    print(is_valid_directory(test_dir))
    try:
        count = get_file_counts(test_dir)
        print(f"Number of files in '{test_dir}': {count}")
    except Exception as e:
        print(f"Error: {e}")