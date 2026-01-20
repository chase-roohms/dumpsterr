"""
Integration and unit tests for main module.
"""
import logging
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import jsonschema

import main as main_module
from observability.metrics import MetricsCollector


class TestSumPathFileCounts:
    """Tests for sum_path_file_counts function."""
    
    def test_sum_single_path(self, test_files_dir):
        """Test summing file counts for single path."""
        logger = logging.getLogger('test')
        paths = [test_files_dir]
        total = main_module.sum_path_file_counts(paths, logger)
        assert total == 5  # 5 files in test_files_dir
    
    def test_sum_multiple_paths(self, test_files_dir, empty_dir):
        """Test summing file counts for multiple paths."""
        logger = logging.getLogger('test')
        paths = [test_files_dir, empty_dir]
        total = main_module.sum_path_file_counts(paths, logger)
        assert total == 5  # 5 + 0
    
    def test_sum_with_invalid_directory(self, test_files_dir, temp_dir):
        """Test that invalid directory raises ValueError."""
        logger = logging.getLogger('test')
        invalid_path = os.path.join(temp_dir, 'nonexistent')
        paths = [test_files_dir, invalid_path]
        
        with pytest.raises(ValueError) as exc_info:
            main_module.sum_path_file_counts(paths, logger)
        assert 'invalid or inaccessible' in str(exc_info.value)
    
    def test_sum_empty_paths_list(self):
        """Test summing with empty paths list."""
        logger = logging.getLogger('test')
        total = main_module.sum_path_file_counts([], logger)
        assert total == 0
    
    def test_sum_logs_debug_messages(self, test_files_dir, caplog):
        """Test that function logs debug messages."""
        logger = logging.getLogger('test')
        logger.setLevel(logging.DEBUG)
        
        with caplog.at_level(logging.DEBUG):
            main_module.sum_path_file_counts([test_files_dir], logger)
        
        assert 'Number of files in' in caplog.text


class TestIsDirsValid:
    """Tests for is_dirs_valid function."""
    
    def test_all_valid_directories(self, test_files_dir, empty_dir):
        """Test validation with all valid directories."""
        logger = logging.getLogger('test')
        directories = [test_files_dir, empty_dir]
        result = main_module.is_dirs_valid(directories, logger)
        assert result is True
    
    def test_one_invalid_directory(self, test_files_dir, temp_dir):
        """Test validation with one invalid directory."""
        logger = logging.getLogger('test')
        invalid_path = os.path.join(temp_dir, 'nonexistent')
        directories = [test_files_dir, invalid_path]
        result = main_module.is_dirs_valid(directories, logger)
        assert result is False
    
    def test_all_invalid_directories(self, temp_dir):
        """Test validation with all invalid directories."""
        logger = logging.getLogger('test')
        directories = [
            os.path.join(temp_dir, 'nonexistent1'),
            os.path.join(temp_dir, 'nonexistent2')
        ]
        result = main_module.is_dirs_valid(directories, logger)
        assert result is False
    
    def test_empty_directories_list(self):
        """Test validation with empty list."""
        logger = logging.getLogger('test')
        result = main_module.is_dirs_valid([], logger)
        assert result is True  # Empty list is valid
    
    def test_logs_error_for_invalid(self, temp_dir, caplog):
        """Test that errors are logged for invalid directories."""
        logger = logging.getLogger('test')
        invalid_path = os.path.join(temp_dir, 'nonexistent')
        
        with caplog.at_level(logging.ERROR):
            main_module.is_dirs_valid([invalid_path], logger)
        
        assert 'invalid or inaccessible' in caplog.text


class TestGetSectionMediaCounts:
    """Tests for get_section_media_counts function."""
    
    def test_get_media_counts(self):
        """Test getting media counts for sections."""
        mock_plex = Mock()
        mock_plex.get_library_size.side_effect = [1000, 500, 250]
        
        sections = {
            'Movies': '1',
            'TV Shows': '2',
            'Music': '3'
        }
        logger = logging.getLogger('test')
        
        result = main_module.get_section_media_counts(mock_plex, sections, logger)
        
        assert result == {
            'Movies': 1000,
            'TV Shows': 500,
            'Music': 250
        }
        assert mock_plex.get_library_size.call_count == 3
    
    def test_empty_sections(self):
        """Test with empty sections dictionary."""
        mock_plex = Mock()
        logger = logging.getLogger('test')
        
        result = main_module.get_section_media_counts(mock_plex, {}, logger)
        
        assert result == {}
        assert mock_plex.get_library_size.call_count == 0
    
    def test_logs_info_messages(self, caplog):
        """Test that info messages are logged."""
        mock_plex = Mock()
        mock_plex.get_library_size.return_value = 100
        
        logger = logging.getLogger('test')
        logger.setLevel(logging.INFO)
        
        with caplog.at_level(logging.INFO):
            main_module.get_section_media_counts(
                mock_plex, 
                {'Movies': '1'}, 
                logger
            )
        
        assert 'Plex Section: Movies, Size: 100' in caplog.text


class TestGetSectionFileCounts:
    """Tests for get_section_file_counts function."""
    
    def test_single_path_per_library(self, test_files_dir, empty_dir):
        """Test getting file counts with single path per library."""
        all_media_info = [
            {'name': 'Movies', 'path': test_files_dir},
            {'name': 'TV Shows', 'path': empty_dir}
        ]
        logger = logging.getLogger('test')
        
        result = main_module.get_section_file_counts(all_media_info, logger)
        
        assert result == {
            'Movies': 5,
            'TV Shows': 0
        }
    
    def test_multiple_paths_per_library(self, test_files_dir, empty_dir):
        """Test getting file counts with multiple paths per library."""
        all_media_info = [
            {'name': 'Movies', 'path': [test_files_dir, empty_dir]}
        ]
        logger = logging.getLogger('test')
        
        result = main_module.get_section_file_counts(all_media_info, logger)
        
        assert result == {'Movies': 5}  # 5 + 0
    
    def test_empty_media_info(self):
        """Test with empty media info list."""
        logger = logging.getLogger('test')
        result = main_module.get_section_file_counts([], logger)
        assert result == {}
    
    def test_string_path_converted_to_list(self, test_files_dir):
        """Test that string paths are converted to lists."""
        all_media_info = [
            {'name': 'Movies', 'path': test_files_dir}
        ]
        logger = logging.getLogger('test')
        
        # Function should handle string path internally
        result = main_module.get_section_file_counts(all_media_info, logger)
        assert 'Movies' in result


class TestProcessLibrary:
    """Tests for process_library function."""
    
    def test_process_library_invalid_directory(self, temp_dir):
        """Test processing library with invalid directory."""
        mock_plex = Mock()
        library = {
            'name': 'Movies',
            'path': [os.path.join(temp_dir, 'nonexistent')],
            'file_count': 100,
            'media_count': 100,
            'section_key': '1'
        }
        logger = logging.getLogger('test')
        
        result = main_module.process_library(mock_plex, library, logger)
        assert result is False
    
    def test_process_library_min_files_not_met(self, test_files_dir):
        """Test processing library when minimum file count not met."""
        mock_plex = Mock()
        library = {
            'name': 'Movies',
            'path': [test_files_dir],
            'file_count': 5,
            'media_count': 100,
            'min_files': 10,  # More than actual
            'section_key': '1'
        }
        logger = logging.getLogger('test')
        
        result = main_module.process_library(mock_plex, library, logger)
        assert result is False
    
    def test_process_library_threshold_not_met(self, test_files_dir):
        """Test processing library when threshold not met."""
        mock_plex = Mock()
        library = {
            'name': 'Movies',
            'path': [test_files_dir],
            'file_count': 50,
            'media_count': 100,
            'min_files': 0,
            'min_threshold': 90,  # 50/100 = 50% < 90%
            'section_key': '1'
        }
        logger = logging.getLogger('test')
        
        result = main_module.process_library(mock_plex, library, logger)
        assert result is False
    
    def test_process_library_successful(self, test_files_dir):
        """Test successfully processing library."""
        mock_plex = Mock()
        mock_plex.empty_section_trash.return_value = True
        
        library = {
            'name': 'Movies',
            'path': [test_files_dir],
            'file_count': 95,
            'media_count': 100,
            'min_files': 10,
            'min_threshold': 90,  # 95/100 = 95% >= 90%
            'section_key': '1'
        }
        logger = logging.getLogger('test')
        
        result = main_module.process_library(mock_plex, library, logger)
        assert result is True
        mock_plex.empty_section_trash.assert_called_once_with('1')
    
    def test_process_library_empty_trash_fails(self, test_files_dir):
        """Test when emptying trash fails."""
        mock_plex = Mock()
        mock_plex.empty_section_trash.return_value = False
        
        library = {
            'name': 'Movies',
            'path': [test_files_dir],
            'file_count': 95,
            'media_count': 100,
            'min_files': 0,
            'min_threshold': 90,
            'section_key': '1'
        }
        logger = logging.getLogger('test')
        
        result = main_module.process_library(mock_plex, library, logger)
        assert result is False
    
    def test_process_library_missing_section_key(self, test_files_dir):
        """Test processing library with missing section key."""
        mock_plex = Mock()
        library = {
            'name': 'Movies',
            'path': [test_files_dir],
            'file_count': 95,
            'media_count': 100,
            'min_files': 0,
            'min_threshold': 90,
            'section_key': None
        }
        logger = logging.getLogger('test')
        
        result = main_module.process_library(mock_plex, library, logger)
        assert result is False
    
    def test_process_library_default_values(self, test_files_dir):
        """Test processing library with default min_files and min_threshold."""
        mock_plex = Mock()
        mock_plex.empty_section_trash.return_value = True
        
        library = {
            'name': 'Movies',
            'path': [test_files_dir],
            'file_count': 100,
            'media_count': 100,
            'section_key': '1'
            # min_files and min_threshold not specified
        }
        logger = logging.getLogger('test')
        
        result = main_module.process_library(mock_plex, library, logger)
        assert result is True
    
    def test_process_library_zero_media_count(self, test_files_dir):
        """Test processing library with zero media count."""
        mock_plex = Mock()
        library = {
            'name': 'Movies',
            'path': [test_files_dir],
            'file_count': 5,
            'media_count': 0,  # Division by zero scenario
            'min_files': 0,
            'min_threshold': 90,
            'section_key': '1'
        }
        logger = logging.getLogger('test')
        
        # Should not crash, should handle division by zero gracefully
        result = main_module.process_library(mock_plex, library, logger)
        # With media_count=0, percentage calculation should be 0%
        assert result is False  # 0% < 90%


class TestMain:
    """Tests for main function."""
    
    @patch('main.plex_client.PlexClient')
    def test_main_successful_execution(self, mock_plex_class, test_files_dir, monkeypatch):
        """Test successful execution of main function."""
        # Setup environment variables
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        # Setup mock Plex client
        mock_plex = Mock()
        mock_plex.get_library_sections.return_value = {'Movies': '1'}
        mock_plex.get_library_size.return_value = 100
        mock_plex.empty_section_trash.return_value = True
        mock_plex_class.return_value = mock_plex
        
        config_data = {
            'libraries': [
                {
                    'name': 'Movies',
                    'path': test_files_dir,
                    'min_files': 0,
                    'min_threshold': 0
                }
            ],
            'settings': {'log_level': 'INFO'}
        }
        
        logger = logging.getLogger('test')
        exit_code = main_module.main(config_data, logger)
        
        assert exit_code == 0  # Success
    
    @patch('main.plex_client.PlexClient')
    def test_main_partial_failure(self, mock_plex_class, test_files_dir, temp_dir, monkeypatch):
        """Test main function with partial failures."""
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        mock_plex = Mock()
        mock_plex.get_library_sections.return_value = {
            'Movies': '1',
            'TV Shows': '2'
        }
        mock_plex.get_library_size.side_effect = [100, 200]
        # First library succeeds, second fails
        mock_plex.empty_section_trash.side_effect = [True, False]
        mock_plex_class.return_value = mock_plex
        
        config_data = {
            'libraries': [
                {
                    'name': 'Movies',
                    'path': test_files_dir,
                    'min_files': 0,
                    'min_threshold': 0
                },
                {
                    'name': 'TV Shows',
                    'path': test_files_dir,  # Use valid path but empty trash will fail
                    'min_files': 0,
                    'min_threshold': 0
                }
            ]
        }
        
        logger = logging.getLogger('test')
        exit_code = main_module.main(config_data, logger)
        
        assert exit_code == 1  # Partial failure
    
    @patch('main.plex_client.PlexClient')
    def test_main_complete_failure(self, mock_plex_class, test_files_dir, monkeypatch):
        """Test main function with complete failure."""
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        mock_plex = Mock()
        mock_plex.get_library_sections.return_value = {'Movies': '1'}
        mock_plex.get_library_size.return_value = 100
        # Empty trash fails
        mock_plex.empty_section_trash.return_value = False
        mock_plex_class.return_value = mock_plex
        
        config_data = {
            'libraries': [
                {
                    'name': 'Movies',
                    'path': test_files_dir,
                    'min_files': 0,
                    'min_threshold': 0
                }
            ]
        }
        
        logger = logging.getLogger('test')
        exit_code = main_module.main(config_data, logger)
        
        assert exit_code == 2  # Complete failure
    
    @patch('main.plex_client.PlexClient')
    def test_main_with_multiple_paths(self, mock_plex_class, test_files_dir, empty_dir, monkeypatch):
        """Test main function with libraries having multiple paths."""
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        mock_plex = Mock()
        mock_plex.get_library_sections.return_value = {'Movies': '1'}
        mock_plex.get_library_size.return_value = 100
        mock_plex.empty_section_trash.return_value = True
        mock_plex_class.return_value = mock_plex
        
        config_data = {
            'libraries': [
                {
                    'name': 'Movies',
                    'path': [test_files_dir, empty_dir],
                    'min_files': 0,
                    'min_threshold': 0
                }
            ]
        }
        
        logger = logging.getLogger('test')
        exit_code = main_module.main(config_data, logger)
        
        assert exit_code == 0
    
    @patch('main.plex_client.PlexClient')
    def test_main_converts_string_paths_to_lists(self, mock_plex_class, test_files_dir, monkeypatch):
        """Test that main converts string paths to lists."""
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        mock_plex = Mock()
        mock_plex.get_library_sections.return_value = {'Movies': '1'}
        mock_plex.get_library_size.return_value = 100
        mock_plex.empty_section_trash.return_value = True
        mock_plex_class.return_value = mock_plex
        
        config_data = {
            'libraries': [
                {
                    'name': 'Movies',
                    'path': test_files_dir,  # String path
                    'min_files': 0,
                    'min_threshold': 0
                }
            ]
        }
        
        logger = logging.getLogger('test')
        exit_code = main_module.main(config_data, logger)
        
        assert exit_code == 0
        # Verify path was converted to list
        assert isinstance(config_data['libraries'][0]['path'], list)
    
    @patch('main.plex_client.PlexClient')
    def test_main_uses_default_logger(self, mock_plex_class, test_files_dir, monkeypatch):
        """Test that main uses default logger when none provided."""
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        mock_plex = Mock()
        mock_plex.get_library_sections.return_value = {'Movies': '1'}
        mock_plex.get_library_size.return_value = 100
        mock_plex.empty_section_trash.return_value = True
        mock_plex_class.return_value = mock_plex
        
        config_data = {
            'libraries': [
                {
                    'name': 'Movies',
                    'path': test_files_dir,
                    'min_files': 0,
                    'min_threshold': 0
                }
            ]
        }
        
        # Call without logger
        exit_code = main_module.main(config_data)
        
        assert exit_code == 0


class TestMainIntegration:
    """Integration tests for the main module workflow."""
    
    @patch('main.plex_client.PlexClient')
    def test_full_workflow(self, mock_plex_class, test_files_dir, monkeypatch):
        """Test complete workflow from config to execution."""
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        # Setup realistic mock responses
        mock_plex = Mock()
        mock_plex.get_library_sections.return_value = {
            'Movies': '1',
            'TV Shows': '2'
        }
        mock_plex.get_library_size.side_effect = [1000, 500]
        mock_plex.empty_section_trash.return_value = True
        mock_plex_class.return_value = mock_plex
        
        config_data = {
            'libraries': [
                {
                    'name': 'Movies',
                    'path': test_files_dir,
                    'min_files': 1,
                    'min_threshold': 0
                },
                {
                    'name': 'TV Shows',
                    'path': test_files_dir,
                    'min_files': 1,
                    'min_threshold': 0
                }
            ],
            'settings': {
                'log_level': 'INFO'
            }
        }
        
        logger = logging.getLogger('test_integration')
        logger.setLevel(logging.INFO)
        
        exit_code = main_module.main(config_data, logger)
        
        # Verify success
        assert exit_code == 0
        
        # Verify Plex client was called correctly
        mock_plex.get_library_sections.assert_called_once()
        assert mock_plex.get_library_size.call_count == 2
        assert mock_plex.empty_section_trash.call_count == 2


class TestMainWithMetrics:
    """Tests for main function with metrics collector integration."""
    
    @patch('main.plex_client.PlexClient')
    def test_main_with_metrics_collector_success(self, mock_plex_class, test_files_dir, temp_dir, monkeypatch):
        """Test main function with metrics collector for successful run."""
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        mock_plex = Mock()
        mock_plex.get_library_sections.return_value = {'Movies': '1'}
        mock_plex.get_library_size.return_value = 100
        mock_plex.empty_section_trash.return_value = True
        mock_plex_class.return_value = mock_plex
        
        config_data = {
            'libraries': [
                {
                    'name': 'Movies',
                    'path': test_files_dir,
                    'min_files': 0,
                    'min_threshold': 0
                }
            ]
        }
        
        logger = logging.getLogger('test')
        metrics_file = str(Path(temp_dir) / 'metrics.json')
        metrics_collector = MetricsCollector(metrics_file)
        
        exit_code = main_module.main(config_data, logger, metrics_collector)
        
        assert exit_code == 0
        
        # Verify metrics were collected
        current_metrics = metrics_collector.get_current_metrics()
        assert current_metrics['start_time'] is not None
        assert current_metrics['end_time'] is not None
        assert current_metrics['exit_code'] == 0
        assert current_metrics['libraries_total'] == 1
        assert current_metrics['libraries_successful'] == 1
        assert current_metrics['libraries_failed'] == 0
        
        # Verify metrics were saved
        assert Path(metrics_file).exists()
    
    @patch('main.plex_client.PlexClient')
    def test_main_with_metrics_collector_partial_failure(self, mock_plex_class, test_files_dir, temp_dir, monkeypatch):
        """Test main function with metrics collector for partial failure."""
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        mock_plex = Mock()
        mock_plex.get_library_sections.return_value = {'Movies': '1', 'TV Shows': '2'}
        mock_plex.get_library_size.side_effect = [100, 100]
        # First succeeds, second fails
        mock_plex.empty_section_trash.side_effect = [True, False]
        mock_plex_class.return_value = mock_plex
        
        config_data = {
            'libraries': [
                {
                    'name': 'Movies',
                    'path': test_files_dir,
                    'min_files': 0,
                    'min_threshold': 0
                },
                {
                    'name': 'TV Shows',
                    'path': test_files_dir,
                    'min_files': 0,
                    'min_threshold': 0
                }
            ]
        }
        
        logger = logging.getLogger('test')
        metrics_file = str(Path(temp_dir) / 'metrics.json')
        metrics_collector = MetricsCollector(metrics_file)
        
        exit_code = main_module.main(config_data, logger, metrics_collector)
        
        assert exit_code == 1  # Partial failure
        
        # Verify metrics were collected
        current_metrics = metrics_collector.get_current_metrics()
        assert current_metrics['exit_code'] == 1
        assert current_metrics['libraries_total'] == 2
        assert current_metrics['libraries_successful'] == 1
        assert current_metrics['libraries_failed'] == 1
        assert len(current_metrics['library_details']) == 2
    
    @patch('main.plex_client.PlexClient')
    def test_main_with_metrics_collector_complete_failure(self, mock_plex_class, test_files_dir, temp_dir, monkeypatch):
        """Test main function with metrics collector for complete failure."""
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        mock_plex = Mock()
        mock_plex.get_library_sections.return_value = {'Movies': '1'}
        mock_plex.get_library_size.return_value = 100
        mock_plex.empty_section_trash.return_value = False
        mock_plex_class.return_value = mock_plex
        
        config_data = {
            'libraries': [
                {
                    'name': 'Movies',
                    'path': test_files_dir,
                    'min_files': 0,
                    'min_threshold': 0
                }
            ]
        }
        
        logger = logging.getLogger('test')
        metrics_file = str(Path(temp_dir) / 'metrics.json')
        metrics_collector = MetricsCollector(metrics_file)
        
        exit_code = main_module.main(config_data, logger, metrics_collector)
        
        assert exit_code == 2  # Complete failure
        
        # Verify metrics were collected
        current_metrics = metrics_collector.get_current_metrics()
        assert current_metrics['exit_code'] == 2
        assert current_metrics['libraries_total'] == 1
        assert current_metrics['libraries_successful'] == 0
        assert current_metrics['libraries_failed'] == 1


class TestCliMain:
    """Tests for cli_main function (CLI entry point)."""
    
    @patch('main.config.get_config')
    @patch('main.setup_logging')
    @patch('main.main')
    @patch('main.plex_client.PlexClient')
    def test_cli_main_success(self, mock_plex_class, mock_main, mock_setup_logging, mock_get_config, monkeypatch):
        """Test cli_main with successful execution."""
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        # Mock config loading
        mock_config = {
            'libraries': [],
            'settings': {
                'log_level': 'DEBUG'
            }
        }
        mock_get_config.return_value = mock_config
        
        # Mock logger
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # Mock main returning success
        mock_main.return_value = 0
        
        exit_code = main_module.cli_main()
        
        assert exit_code == 0
        mock_get_config.assert_called_once()
        mock_setup_logging.assert_called_once_with(
            log_level='DEBUG',
            log_format='standard',
            log_file=None
        )
        mock_main.assert_called_once()
    
    @patch('main.config.get_config')
    @patch('main.setup_logging')
    @patch('main.main')
    def test_cli_main_with_json_logging(self, mock_main, mock_setup_logging, mock_get_config, monkeypatch):
        """Test cli_main with JSON logging format."""
        monkeypatch.setenv('LOG_FORMAT', 'json')
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        mock_config = {
            'libraries': [],
            'settings': {
                'log_level': 'INFO'
            }
        }
        mock_get_config.return_value = mock_config
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        mock_main.return_value = 0
        
        exit_code = main_module.cli_main()
        
        assert exit_code == 0
        mock_setup_logging.assert_called_once_with(
            log_level='INFO',
            log_format='json',
            log_file=None
        )
    
    @patch('main.config.get_config')
    @patch('main.setup_logging')
    @patch('main.main')
    def test_cli_main_with_log_file(self, mock_main, mock_setup_logging, mock_get_config, monkeypatch):
        """Test cli_main with log file rotation enabled."""
        monkeypatch.setenv('LOG_FILE', '/var/log/app.log')
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        mock_config = {
            'libraries': [],
            'settings': {
                'log_level': 'WARNING'
            }
        }
        mock_get_config.return_value = mock_config
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        mock_main.return_value = 0
        
        exit_code = main_module.cli_main()
        
        assert exit_code == 0
        mock_setup_logging.assert_called_once_with(
            log_level='WARNING',
            log_format='standard',
            log_file='/var/log/app.log'
        )
    
    @patch('main.config.get_config')
    @patch('main.setup_logging')
    @patch('main.main')
    def test_cli_main_default_log_level(self, mock_main, mock_setup_logging, mock_get_config, monkeypatch):
        """Test cli_main uses default log level when not specified."""
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        # Config without settings
        mock_config = {
            'libraries': []
        }
        mock_get_config.return_value = mock_config
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        mock_main.return_value = 0
        
        exit_code = main_module.cli_main()
        
        assert exit_code == 0
        mock_setup_logging.assert_called_once_with(
            log_level='INFO',  # Default
            log_format='standard',
            log_file=None
        )
    
    @patch('main.config.get_config')
    def test_cli_main_config_validation_error(self, mock_get_config, capsys):
        """Test cli_main handles config validation errors."""
        mock_get_config.side_effect = jsonschema.ValidationError('Invalid config')
        
        exit_code = main_module.cli_main()
        
        assert exit_code == 1
        captured = capsys.readouterr()
        assert 'Failed to load configuration' in captured.out
        assert 'Invalid config' in captured.out
    
    @patch('main.config.get_config')
    def test_cli_main_config_file_not_found(self, mock_get_config, capsys):
        """Test cli_main handles missing config file."""
        mock_get_config.side_effect = FileNotFoundError('Config file not found')
        
        exit_code = main_module.cli_main()
        
        assert exit_code == 1
        captured = capsys.readouterr()
        assert 'Failed to load configuration' in captured.out
        assert 'Config file not found' in captured.out
    
    @patch('main.config.get_config')
    def test_cli_main_config_permission_error(self, mock_get_config, capsys):
        """Test cli_main handles permission errors."""
        mock_get_config.side_effect = PermissionError('Permission denied')
        
        exit_code = main_module.cli_main()
        
        assert exit_code == 1
        captured = capsys.readouterr()
        assert 'Failed to load configuration' in captured.out
        assert 'Permission denied' in captured.out
    
    @patch('main.config.get_config')
    def test_cli_main_config_is_directory_error(self, mock_get_config, capsys):
        """Test cli_main handles directory instead of file error."""
        mock_get_config.side_effect = IsADirectoryError('Is a directory')
        
        exit_code = main_module.cli_main()
        
        assert exit_code == 1
        captured = capsys.readouterr()
        assert 'Failed to load configuration' in captured.out
        assert 'Is a directory' in captured.out
    
    @patch('main.config.get_config')
    @patch('main.setup_logging')
    @patch('main.main')
    @patch('main.MetricsCollector')
    def test_cli_main_initializes_metrics_collector(self, mock_metrics_class, mock_main, mock_setup_logging, mock_get_config, monkeypatch):
        """Test cli_main initializes metrics collector."""
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        mock_config = {'libraries': [], 'settings': {'log_level': 'INFO'}}
        mock_get_config.return_value = mock_config
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        mock_metrics = Mock()
        mock_metrics_class.return_value = mock_metrics
        mock_main.return_value = 0
        
        exit_code = main_module.cli_main()
        
        assert exit_code == 0
        mock_metrics_class.assert_called_once()
        # Verify metrics collector was passed to main
        mock_main.assert_called_once_with(mock_config, mock_logger, mock_metrics)
    
    @patch('main.config.get_config')
    @patch('main.setup_logging')
    @patch('main.main')
    def test_cli_main_returns_main_exit_code(self, mock_main, mock_setup_logging, mock_get_config, monkeypatch):
        """Test cli_main returns the exit code from main."""
        monkeypatch.setenv('PLEX_URL', 'http://localhost:32400')
        monkeypatch.setenv('PLEX_TOKEN', 'test_token')
        
        mock_config = {'libraries': [], 'settings': {}}
        mock_get_config.return_value = mock_config
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # Test different exit codes
        for expected_code in [0, 1, 2]:
            mock_main.return_value = expected_code
            exit_code = main_module.cli_main()
            assert exit_code == expected_code
