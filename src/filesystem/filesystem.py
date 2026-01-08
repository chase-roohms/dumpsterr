import os
from pathlib import Path

def _validate_directory(path: str):
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

def get_file_counts(directory: str):
    '''
    Get the count of files in the specified directory.
    
    :param directory: Path to the directory
    :return: Number of files in the directory
    '''
    _validate_directory(directory)
    dir_path = Path(directory)
    return len([f for f in dir_path.iterdir() if f.is_file()])

if __name__ == "__main__":
    # Example usage / testing
    test_dir = 'data'
    try:
        count = get_file_counts(test_dir)
        print(f"Number of files in '{test_dir}': {count}")
    except Exception as e:
        print(f"Error: {e}")