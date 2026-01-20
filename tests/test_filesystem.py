"""
Unit tests for filesystem module.
"""
import os
import pytest
from pathlib import Path

import filesystem.filesystem as filesystem_module


class TestValidateDirectory:
    """Tests for _validate_directory function."""
    
    def test_valid_directory(self, test_files_dir):
        """Test validating an existing, readable directory."""
        # Should not raise any exception
        filesystem_module._validate_directory(test_files_dir)
    
    def test_directory_does_not_exist(self, temp_dir):
        """Test validating a non-existent directory."""
        non_existent = os.path.join(temp_dir, 'does_not_exist')
        with pytest.raises(FileNotFoundError) as exc_info:
            filesystem_module._validate_directory(non_existent)
        assert 'Directory does not exist' in str(exc_info.value)
    
    def test_path_is_not_directory(self, temp_dir):
        """Test validating a file path instead of directory."""
        file_path = Path(temp_dir) / 'file.txt'
        file_path.write_text('content')
        with pytest.raises(NotADirectoryError) as exc_info:
            filesystem_module._validate_directory(str(file_path))
        assert 'Path is not a directory' in str(exc_info.value)
    
    def test_directory_not_readable(self, temp_dir):
        """Test validating a directory without read permissions."""
        restricted_dir = Path(temp_dir) / 'restricted'
        restricted_dir.mkdir()
        
        # Remove read permissions
        os.chmod(restricted_dir, 0o000)
        
        try:
            with pytest.raises(PermissionError) as exc_info:
                filesystem_module._validate_directory(str(restricted_dir))
            assert 'Read permission denied' in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            os.chmod(restricted_dir, 0o755)
    
    def test_validate_nested_directory(self, nested_test_dir):
        """Test validating a nested directory structure."""
        # Should not raise any exception
        filesystem_module._validate_directory(nested_test_dir)
        
        # Also test nested subdirectories
        level1 = os.path.join(nested_test_dir, 'level1')
        level2 = os.path.join(level1, 'level2')
        
        filesystem_module._validate_directory(level1)
        filesystem_module._validate_directory(level2)
    
    def test_validate_empty_directory(self, empty_dir):
        """Test validating an empty directory."""
        # Should not raise - empty directories are valid
        filesystem_module._validate_directory(empty_dir)


class TestIsValidDirectory:
    """Tests for is_valid_directory function."""
    
    def test_valid_directory_returns_true(self, test_files_dir):
        """Test that a valid directory returns True and empty error."""
        is_valid, error = filesystem_module.is_valid_directory(test_files_dir)
        assert is_valid is True
        assert error == ''
    
    def test_non_existent_directory_returns_false(self, temp_dir):
        """Test that non-existent directory returns False with error."""
        non_existent = os.path.join(temp_dir, 'does_not_exist')
        is_valid, error = filesystem_module.is_valid_directory(non_existent)
        assert is_valid is False
        assert 'Directory does not exist' in error
    
    def test_file_path_returns_false(self, temp_dir):
        """Test that file path returns False with error."""
        file_path = Path(temp_dir) / 'file.txt'
        file_path.write_text('content')
        is_valid, error = filesystem_module.is_valid_directory(str(file_path))
        assert is_valid is False
        assert 'Path is not a directory' in error
    
    def test_unreadable_directory_returns_false(self, temp_dir):
        """Test that unreadable directory returns False with error."""
        restricted_dir = Path(temp_dir) / 'restricted'
        restricted_dir.mkdir()
        os.chmod(restricted_dir, 0o000)
        
        try:
            is_valid, error = filesystem_module.is_valid_directory(str(restricted_dir))
            assert is_valid is False
            assert 'Read permission denied' in error
        finally:
            os.chmod(restricted_dir, 0o755)
    
    def test_empty_directory_is_valid(self, empty_dir):
        """Test that empty directory is valid."""
        is_valid, error = filesystem_module.is_valid_directory(empty_dir)
        assert is_valid is True
        assert error == ''
    
    def test_relative_path(self, test_files_dir):
        """Test with relative path."""
        # Change to parent directory
        original_cwd = os.getcwd()
        try:
            parent = Path(test_files_dir).parent
            os.chdir(parent)
            relative_path = Path(test_files_dir).name
            is_valid, error = filesystem_module.is_valid_directory(relative_path)
            assert is_valid is True
            assert error == ''
        finally:
            os.chdir(original_cwd)
    
    def test_absolute_path(self, test_files_dir):
        """Test with absolute path."""
        absolute_path = os.path.abspath(test_files_dir)
        is_valid, error = filesystem_module.is_valid_directory(absolute_path)
        assert is_valid is True
        assert error == ''


class TestGetFileCounts:
    """Tests for get_file_counts function."""
    
    def test_count_files_in_directory(self, test_files_dir):
        """Test counting files in a directory."""
        count = filesystem_module.get_file_counts(test_files_dir)
        assert count == 5  # We created 5 files in the fixture
    
    def test_count_empty_directory(self, empty_dir):
        """Test counting files in an empty directory."""
        count = filesystem_module.get_file_counts(empty_dir)
        assert count == 0
    
    def test_count_includes_subdirectories(self, nested_test_dir):
        """Test that count includes subdirectories."""
        count = filesystem_module.get_file_counts(nested_test_dir)
        # Should count: file1.txt, level1/ (directory counts as 1 item)
        assert count == 2  # 1 file + 1 subdirectory at root level
    
    def test_count_with_hidden_files(self, temp_dir):
        """Test counting with hidden files."""
        test_dir = Path(temp_dir) / 'hidden_test'
        test_dir.mkdir()
        
        # Create regular and hidden files
        (test_dir / 'regular.txt').write_text('content')
        (test_dir / '.hidden').write_text('hidden content')
        
        count = filesystem_module.get_file_counts(str(test_dir))
        assert count == 2  # Both regular and hidden files
    
    def test_count_mixed_content(self, temp_dir):
        """Test counting directory with mixed files and subdirectories."""
        test_dir = Path(temp_dir) / 'mixed'
        test_dir.mkdir()
        
        # Create files
        (test_dir / 'file1.txt').write_text('content1')
        (test_dir / 'file2.txt').write_text('content2')
        
        # Create subdirectories
        (test_dir / 'subdir1').mkdir()
        (test_dir / 'subdir2').mkdir()
        
        count = filesystem_module.get_file_counts(str(test_dir))
        assert count == 4  # 2 files + 2 directories
    
    def test_count_with_symlinks(self, temp_dir):
        """Test counting with symbolic links."""
        test_dir = Path(temp_dir) / 'symlink_test'
        test_dir.mkdir()
        
        # Create a file and a symlink to it
        file_path = test_dir / 'original.txt'
        file_path.write_text('content')
        
        link_path = test_dir / 'link.txt'
        try:
            link_path.symlink_to(file_path)
            
            count = filesystem_module.get_file_counts(str(test_dir))
            assert count == 2  # Original file + symlink
        except OSError:
            # Skip if symlinks not supported on this system
            pytest.skip("Symbolic links not supported on this system")
    
    def test_count_non_existent_directory_raises_error(self, temp_dir):
        """Test that counting non-existent directory raises error."""
        non_existent = os.path.join(temp_dir, 'does_not_exist')
        with pytest.raises(FileNotFoundError):
            filesystem_module.get_file_counts(non_existent)
    
    def test_count_file_path_raises_error(self, temp_dir):
        """Test that passing file path raises error."""
        file_path = Path(temp_dir) / 'file.txt'
        file_path.write_text('content')
        with pytest.raises(NotADirectoryError):
            filesystem_module.get_file_counts(str(file_path))
    
    def test_count_various_file_types(self, temp_dir):
        """Test counting with various file types."""
        test_dir = Path(temp_dir) / 'various_types'
        test_dir.mkdir()
        
        # Create various file types
        (test_dir / 'text.txt').write_text('text')
        (test_dir / 'data.json').write_text('{}')
        (test_dir / 'script.py').write_text('# python')
        (test_dir / 'config.yml').write_text('key: value')
        (test_dir / 'no_extension').write_text('data')
        
        count = filesystem_module.get_file_counts(str(test_dir))
        assert count == 5


class TestFilesystemIntegration:
    """Integration tests for filesystem module."""
    
    def test_validate_and_count_workflow(self, test_files_dir):
        """Test complete workflow of validation and counting."""
        # First validate
        is_valid, error = filesystem_module.is_valid_directory(test_files_dir)
        assert is_valid is True
        assert error == ''
        
        # Then count
        count = filesystem_module.get_file_counts(test_files_dir)
        assert count > 0
    
    def test_multiple_directory_validation(self, test_files_dir, empty_dir, nested_test_dir):
        """Test validating multiple directories."""
        directories = [test_files_dir, empty_dir, nested_test_dir]
        
        for directory in directories:
            is_valid, error = filesystem_module.is_valid_directory(directory)
            assert is_valid is True, f"Directory {directory} should be valid: {error}"
    
    def test_error_handling_chain(self, temp_dir):
        """Test that validation catches errors before counting."""
        non_existent = os.path.join(temp_dir, 'does_not_exist')
        
        # Validation should catch the error
        is_valid, error = filesystem_module.is_valid_directory(non_existent)
        assert is_valid is False
        assert error != ''
        
        # Counting should also raise
        with pytest.raises(FileNotFoundError):
            filesystem_module.get_file_counts(non_existent)
    
    def test_special_characters_in_path(self, temp_dir):
        """Test handling paths with special characters."""
        special_dir = Path(temp_dir) / 'dir with spaces & special!chars'
        special_dir.mkdir()
        (special_dir / 'file.txt').write_text('content')
        
        is_valid, error = filesystem_module.is_valid_directory(str(special_dir))
        assert is_valid is True
        
        count = filesystem_module.get_file_counts(str(special_dir))
        assert count == 1
    
    def test_deeply_nested_structure(self, temp_dir):
        """Test with deeply nested directory structure."""
        base = Path(temp_dir) / 'deep'
        current = base
        
        # Create 10 levels deep
        for i in range(10):
            current = current / f'level{i}'
            current.mkdir(parents=True)
            (current / f'file{i}.txt').write_text(f'level {i}')
        
        # Validate each level
        current = base
        for i in range(10):
            current = current / f'level{i}'
            is_valid, error = filesystem_module.is_valid_directory(str(current))
            assert is_valid is True
    
    def test_unicode_filenames(self, temp_dir):
        """Test handling unicode characters in filenames."""
        unicode_dir = Path(temp_dir) / 'unicode_test'
        unicode_dir.mkdir()
        
        # Create files with unicode names
        (unicode_dir / 'файл.txt').write_text('content')
        (unicode_dir / '文件.txt').write_text('content')
        (unicode_dir / 'αρχείο.txt').write_text('content')
        
        is_valid, error = filesystem_module.is_valid_directory(str(unicode_dir))
        assert is_valid is True
        
        count = filesystem_module.get_file_counts(str(unicode_dir))
        assert count == 3
