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


class TestSymlinkSupport:
    """Tests for symlink support in filesystem module."""
    
    def test_validate_symlink_to_directory(self, temp_dir):
        """Test validating a symlink that points to a valid directory."""
        target_dir = Path(temp_dir) / 'target'
        target_dir.mkdir()
        (target_dir / 'file.txt').write_text('content')
        
        link_dir = Path(temp_dir) / 'link'
        try:
            link_dir.symlink_to(target_dir)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        # Should validate successfully
        filesystem_module._validate_directory(str(link_dir))
    
    def test_is_valid_symlink_to_directory(self, temp_dir):
        """Test is_valid_directory with symlink to valid directory."""
        target_dir = Path(temp_dir) / 'target'
        target_dir.mkdir()
        
        link_dir = Path(temp_dir) / 'link'
        try:
            link_dir.symlink_to(target_dir)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        is_valid, error = filesystem_module.is_valid_directory(str(link_dir))
        assert is_valid is True
        assert error == ''
    
    def test_broken_symlink_raises_error(self, temp_dir):
        """Test that broken symlink raises FileNotFoundError."""
        target_dir = Path(temp_dir) / 'target'
        target_dir.mkdir()
        
        link_dir = Path(temp_dir) / 'link'
        try:
            link_dir.symlink_to(target_dir)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        # Remove the target to break the symlink
        target_dir.rmdir()
        
        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError) as exc_info:
            filesystem_module._validate_directory(str(link_dir))
        assert 'Symlink target does not exist' in str(exc_info.value) or 'Broken symlink' in str(exc_info.value)
    
    def test_is_valid_broken_symlink(self, temp_dir):
        """Test is_valid_directory with broken symlink."""
        target_dir = Path(temp_dir) / 'target'
        target_dir.mkdir()
        
        link_dir = Path(temp_dir) / 'link'
        try:
            link_dir.symlink_to(target_dir)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        # Remove the target to break the symlink
        target_dir.rmdir()
        
        is_valid, error = filesystem_module.is_valid_directory(str(link_dir))
        assert is_valid is False
        assert 'Symlink target does not exist' in error or 'Broken symlink' in error
    
    def test_symlink_to_file_raises_error(self, temp_dir):
        """Test that symlink to a file raises NotADirectoryError."""
        target_file = Path(temp_dir) / 'target.txt'
        target_file.write_text('content')
        
        link_path = Path(temp_dir) / 'link'
        try:
            link_path.symlink_to(target_file)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        # Should raise NotADirectoryError
        with pytest.raises(NotADirectoryError) as exc_info:
            filesystem_module._validate_directory(str(link_path))
        assert 'not a directory' in str(exc_info.value).lower()
    
    def test_is_valid_symlink_to_file(self, temp_dir):
        """Test is_valid_directory with symlink to file."""
        target_file = Path(temp_dir) / 'target.txt'
        target_file.write_text('content')
        
        link_path = Path(temp_dir) / 'link'
        try:
            link_path.symlink_to(target_file)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        is_valid, error = filesystem_module.is_valid_directory(str(link_path))
        assert is_valid is False
        assert 'not a directory' in error.lower()
    
    def test_symlink_to_nonexistent_path(self, temp_dir):
        """Test symlink pointing to non-existent path."""
        link_path = Path(temp_dir) / 'link'
        non_existent = Path(temp_dir) / 'does_not_exist'
        
        try:
            link_path.symlink_to(non_existent)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError) as exc_info:
            filesystem_module._validate_directory(str(link_path))
        assert 'Symlink target does not exist' in str(exc_info.value) or 'Broken symlink' in str(exc_info.value)
    
    def test_nested_symlinks(self, temp_dir):
        """Test symlinks pointing to other symlinks."""
        target_dir = Path(temp_dir) / 'target'
        target_dir.mkdir()
        
        link1 = Path(temp_dir) / 'link1'
        link2 = Path(temp_dir) / 'link2'
        
        try:
            link1.symlink_to(target_dir)
            link2.symlink_to(link1)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        # Should follow chain and validate successfully
        filesystem_module._validate_directory(str(link2))
        
        is_valid, error = filesystem_module.is_valid_directory(str(link2))
        assert is_valid is True
        assert error == ''
    
    def test_circular_symlink_raises_error(self, temp_dir):
        """Test circular symlink reference."""
        link1 = Path(temp_dir) / 'link1'
        link2 = Path(temp_dir) / 'link2'
        
        try:
            link1.symlink_to(link2)
            link2.symlink_to(link1)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        # Should raise an error (FileNotFoundError or RuntimeError)
        with pytest.raises(FileNotFoundError) as exc_info:
            filesystem_module._validate_directory(str(link1))
        assert 'Broken symlink' in str(exc_info.value) or 'circular' in str(exc_info.value).lower()
    
    def test_symlink_permissions(self, temp_dir):
        """Test symlink pointing to directory without read permissions."""
        target_dir = Path(temp_dir) / 'target'
        target_dir.mkdir()
        
        link_dir = Path(temp_dir) / 'link'
        try:
            link_dir.symlink_to(target_dir)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        # Remove read permissions from target
        os.chmod(target_dir, 0o000)
        
        try:
            with pytest.raises(PermissionError) as exc_info:
                filesystem_module._validate_directory(str(link_dir))
            assert 'Read permission denied' in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            os.chmod(target_dir, 0o755)
    
    def test_count_files_through_symlink(self, temp_dir):
        """Test counting files in a directory accessed via symlink."""
        target_dir = Path(temp_dir) / 'target'
        target_dir.mkdir()
        (target_dir / 'file1.txt').write_text('content1')
        (target_dir / 'file2.txt').write_text('content2')
        (target_dir / 'file3.txt').write_text('content3')
        
        link_dir = Path(temp_dir) / 'link'
        try:
            link_dir.symlink_to(target_dir)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        # Should count files through symlink
        count = filesystem_module.get_file_counts(str(link_dir))
        assert count == 3
    
    def test_symlink_absolute_path(self, temp_dir):
        """Test symlink with absolute path target."""
        target_dir = Path(temp_dir) / 'target'
        target_dir.mkdir()
        
        link_dir = Path(temp_dir) / 'link'
        try:
            link_dir.symlink_to(target_dir.resolve())
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        is_valid, error = filesystem_module.is_valid_directory(str(link_dir))
        assert is_valid is True
        assert error == ''
    
    def test_symlink_relative_path(self, temp_dir):
        """Test symlink with relative path target."""
        target_dir = Path(temp_dir) / 'target'
        target_dir.mkdir()
        
        # Create link in subdirectory with relative path
        subdir = Path(temp_dir) / 'subdir'
        subdir.mkdir()
        link_dir = subdir / 'link'
        
        try:
            link_dir.symlink_to('../target')
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        is_valid, error = filesystem_module.is_valid_directory(str(link_dir))
        assert is_valid is True
        assert error == ''
    
    def test_symlink_chain_with_broken_link(self, temp_dir):
        """Test chain of symlinks where intermediate link is broken."""
        target_dir = Path(temp_dir) / 'target'
        target_dir.mkdir()
        
        link1 = Path(temp_dir) / 'link1'
        link2 = Path(temp_dir) / 'link2'
        
        try:
            link1.symlink_to(target_dir)
            link2.symlink_to(link1)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        # Remove target to break the chain
        target_dir.rmdir()
        
        # Should detect broken chain
        with pytest.raises(FileNotFoundError):
            filesystem_module._validate_directory(str(link2))
    
    def test_count_excludes_broken_symlinks(self, temp_dir):
        """Test that broken symlinks are excluded from file count."""
        test_dir = Path(temp_dir) / 'mixed_links'
        test_dir.mkdir()
        
        # Create regular files
        (test_dir / 'regular1.txt').write_text('content1')
        (test_dir / 'regular2.txt').write_text('content2')
        
        # Create valid symlink
        target_dir = Path(temp_dir) / 'valid_target'
        target_dir.mkdir()
        valid_link = test_dir / 'valid_link'
        
        # Create broken symlink
        broken_target = Path(temp_dir) / 'broken_target'
        broken_target.mkdir()
        broken_link = test_dir / 'broken_link'
        
        try:
            valid_link.symlink_to(target_dir)
            broken_link.symlink_to(broken_target)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        # Remove target to break the symlink
        broken_target.rmdir()
        
        # Count should exclude broken symlink
        # Expected: 2 regular files + 1 valid symlink = 3
        count = filesystem_module.get_file_counts(str(test_dir))
        assert count == 3, f"Expected 3 (2 regular + 1 valid symlink), got {count}"
    
    def test_count_all_broken_symlinks(self, temp_dir):
        """Test directory with only broken symlinks."""
        test_dir = Path(temp_dir) / 'all_broken'
        test_dir.mkdir()
        
        # Create multiple broken symlinks
        for i in range(3):
            target = Path(temp_dir) / f'missing_target_{i}'
            link = test_dir / f'broken_link_{i}'
            try:
                link.symlink_to(target)
            except OSError:
                pytest.skip("Symbolic links not supported on this system")
        
        # All symlinks are broken, count should be 0
        count = filesystem_module.get_file_counts(str(test_dir))
        assert count == 0, f"Expected 0 (all broken symlinks), got {count}"
    
    def test_count_mixed_valid_and_broken_symlinks(self, temp_dir):
        """Test counting with mix of valid files, valid symlinks, and broken symlinks."""
        test_dir = Path(temp_dir) / 'complex_mix'
        test_dir.mkdir()
        
        # Create regular files
        (test_dir / 'file1.txt').write_text('content')
        (test_dir / 'file2.txt').write_text('content')
        
        # Create regular subdirectory
        (test_dir / 'subdir').mkdir()
        
        # Create valid symlinks
        valid_target1 = Path(temp_dir) / 'valid1'
        valid_target1.mkdir()
        valid_link1 = test_dir / 'valid_link1'
        
        valid_target2 = Path(temp_dir) / 'valid2.txt'
        valid_target2.write_text('content')
        valid_link2 = test_dir / 'valid_link2'
        
        # Create broken symlinks
        broken_target1 = Path(temp_dir) / 'broken1'
        broken_target1.mkdir()
        broken_link1 = test_dir / 'broken_link1'
        
        broken_target2 = Path(temp_dir) / 'broken2.txt'
        broken_target2.write_text('content')
        broken_link2 = test_dir / 'broken_link2'
        
        try:
            valid_link1.symlink_to(valid_target1)
            valid_link2.symlink_to(valid_target2)
            broken_link1.symlink_to(broken_target1)
            broken_link2.symlink_to(broken_target2)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        # Break some symlinks
        broken_target1.rmdir()
        broken_target2.unlink()
        
        # Count: 2 regular files + 1 subdir + 2 valid symlinks = 5
        count = filesystem_module.get_file_counts(str(test_dir))
        assert count == 5, f"Expected 5 (2 files + 1 dir + 2 valid symlinks), got {count}"
    
    def test_count_circular_symlinks_excluded(self, temp_dir):
        """Test that circular symlinks are excluded from count."""
        test_dir = Path(temp_dir) / 'circular_test'
        test_dir.mkdir()
        
        # Create regular file
        (test_dir / 'regular.txt').write_text('content')
        
        # Create circular symlinks
        link1 = test_dir / 'link1'
        link2 = test_dir / 'link2'
        
        try:
            link1.symlink_to(link2)
            link2.symlink_to(link1)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        # Count should exclude circular symlinks, only count regular file
        count = filesystem_module.get_file_counts(str(test_dir))
        assert count == 1, f"Expected 1 (1 regular file, circular symlinks excluded), got {count}"

