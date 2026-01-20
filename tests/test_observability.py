"""Tests for observability module."""

import json
import logging
from pathlib import Path
import pytest
from observability.logging_config import StructuredFormatter, setup_logging
from observability.metrics import MetricsCollector


class TestStructuredFormatter:
    """Tests for StructuredFormatter."""
    
    def test_format_simple_message(self):
        """Test formatting a simple log message."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data['level'] == 'INFO'
        assert data['logger'] == 'test'
        assert data['message'] == 'Test message'
        assert 'timestamp' in data
    
    def test_format_with_extra_fields(self):
        """Test formatting with extra fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Library processed",
            args=(),
            exc_info=None
        )
        record.library_name = "Movies"
        record.file_count = 100
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data['library_name'] == 'Movies'
        assert data['file_count'] == 100
    
    def test_format_with_exception(self):
        """Test formatting a log record with exception info."""
        formatter = StructuredFormatter()
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
            
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=10,
                msg="An error occurred",
                args=(),
                exc_info=exc_info
            )
            
            result = formatter.format(record)
            data = json.loads(result)
            
            assert data['level'] == 'ERROR'
            assert data['message'] == 'An error occurred'
            assert 'exception' in data
            assert 'ValueError: Test exception' in data['exception']
    
    def test_format_with_media_count(self):
        """Test formatting with media_count field."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Processing complete",
            args=(),
            exc_info=None
        )
        record.library_name = "TV Shows"
        record.file_count = 50
        record.media_count = 45
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data['library_name'] == 'TV Shows'
        assert data['file_count'] == 50
        assert data['media_count'] == 45


class TestSetupLogging:
    """Tests for setup_logging."""
    
    def test_setup_standard_logging(self):
        """Test standard logging setup."""
        logger = setup_logging(log_level='INFO', log_format='standard')
        
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0
    
    def test_setup_json_logging(self):
        """Test JSON logging setup."""
        logger = setup_logging(log_level='DEBUG', log_format='json')
        
        assert logger.level == logging.DEBUG
        # Verify JSON formatter is used
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, StructuredFormatter)
    
    def test_setup_with_log_file(self, temp_dir):
        """Test logging setup with file output."""
        log_file = str(Path(temp_dir) / 'test.log')
        logger = setup_logging(log_level='INFO', log_file=log_file)
        
        # Should have console + file handlers
        assert len(logger.handlers) == 2
        assert Path(log_file).exists()


class TestMetricsCollector:
    """Tests for MetricsCollector."""
    
    def test_initialization(self, temp_dir):
        """Test metrics collector initialization."""
        metrics_file = str(Path(temp_dir) / 'metrics.json')
        collector = MetricsCollector(metrics_file)
        
        assert collector.metrics_file == Path(metrics_file)
        assert collector.current_run['libraries_total'] == 0
    
    def test_start_end_run(self, temp_dir):
        """Test run lifecycle tracking."""
        metrics_file = str(Path(temp_dir) / 'metrics.json')
        collector = MetricsCollector(metrics_file)
        
        collector.start_run()
        assert collector.current_run['start_time'] is not None
        
        collector.end_run(0)
        assert collector.current_run['end_time'] is not None
        assert collector.current_run['exit_code'] == 0
        assert collector.current_run['duration_seconds'] is not None
    
    def test_add_library_result(self, temp_dir):
        """Test adding library results."""
        metrics_file = str(Path(temp_dir) / 'metrics.json')
        collector = MetricsCollector(metrics_file)
        
        collector.add_library_result(
            name='Movies',
            success=True,
            file_count=100,
            media_count=95,
            threshold_percentage=105.26
        )
        
        assert collector.current_run['libraries_total'] == 1
        assert collector.current_run['libraries_successful'] == 1
        assert len(collector.current_run['library_details']) == 1
        
        detail = collector.current_run['library_details'][0]
        assert detail['name'] == 'Movies'
        assert detail['success'] is True
        assert detail['file_count'] == 100
    
    def test_save_metrics(self, temp_dir):
        """Test metrics persistence."""
        metrics_file = str(Path(temp_dir) / 'metrics.json')
        collector = MetricsCollector(metrics_file)
        
        collector.start_run()
        collector.add_library_result(
            name='Movies',
            success=True,
            file_count=100,
            media_count=95,
            threshold_percentage=105.26
        )
        collector.end_run(0)
        collector.save_metrics()
        
        # Verify file was created
        assert Path(metrics_file).exists()
        
        # Load and verify contents
        with open(metrics_file, 'r') as f:
            data = json.load(f)
        
        assert data['summary']['total_runs'] == 1
        assert data['summary']['successful_runs'] == 1
        assert len(data['runs']) == 1
    
    def test_metrics_accumulation(self, temp_dir):
        """Test that metrics accumulate across multiple runs."""
        metrics_file = str(Path(temp_dir) / 'metrics.json')
        
        # First run
        collector1 = MetricsCollector(metrics_file)
        collector1.start_run()
        collector1.add_library_result('Movies', True, 100, 95, 105.26)
        collector1.end_run(0)
        collector1.save_metrics()
        
        # Second run
        collector2 = MetricsCollector(metrics_file)
        collector2.start_run()
        collector2.add_library_result('TV Shows', False, 50, 100, 50.0, 'Threshold not met')
        collector2.end_run(1)
        collector2.save_metrics()
        
        # Verify accumulation
        with open(metrics_file, 'r') as f:
            data = json.load(f)
        
        assert data['summary']['total_runs'] == 2
        assert data['summary']['successful_runs'] == 1
        assert data['summary']['partial_runs'] == 1
        assert len(data['runs']) == 2
    
    def test_load_latest_metrics(self, temp_dir):
        """Test loading latest metrics."""
        metrics_file = str(Path(temp_dir) / 'metrics.json')
        
        # Create some metrics
        collector = MetricsCollector(metrics_file)
        collector.start_run()
        collector.end_run(0)
        collector.save_metrics()
        
        # Load metrics
        loaded = MetricsCollector.load_latest_metrics(metrics_file)
        
        assert loaded is not None
        assert 'summary' in loaded
        assert 'runs' in loaded
    
    def test_load_latest_metrics_nonexistent(self, temp_dir):
        """Test loading metrics when file doesn't exist."""
        metrics_file = str(Path(temp_dir) / 'nonexistent.json')
        loaded = MetricsCollector.load_latest_metrics(metrics_file)
        
        assert loaded is None
    
    def test_run_history_limit(self, temp_dir):
        """Test that run history is limited to 100 entries."""
        metrics_file = str(Path(temp_dir) / 'metrics.json')
        
        # Create 105 runs
        for i in range(105):
            collector = MetricsCollector(metrics_file)
            collector.start_run()
            collector.end_run(0)
            collector.save_metrics()
        
        # Verify only last 100 are kept
        with open(metrics_file, 'r') as f:
            data = json.load(f)
        
        assert data['summary']['total_runs'] == 105
        assert len(data['runs']) == 100
    
    def test_save_metrics_with_permission_error(self, temp_dir, caplog):
        """Test metrics save gracefully handles permission errors."""
        import os
        import stat
        
        metrics_file = str(Path(temp_dir) / 'readonly' / 'metrics.json')
        collector = MetricsCollector(metrics_file)
        collector.start_run()
        collector.end_run(0)
        
        # Create parent directory but make it read-only
        os.makedirs(Path(metrics_file).parent, exist_ok=True)
        os.chmod(Path(metrics_file).parent, stat.S_IRUSR | stat.S_IXUSR)
        
        try:
            with caplog.at_level(logging.WARNING):
                collector.save_metrics()
            
            # Should have logged a warning but not raised an exception
            assert any('Failed to save metrics' in record.message for record in caplog.records)
        finally:
            # Restore permissions for cleanup
            os.chmod(Path(metrics_file).parent, stat.S_IRWXU)
    
    def test_load_corrupted_json_file(self, temp_dir):
        """Test loading metrics when JSON file is corrupted."""
        metrics_file = str(Path(temp_dir) / 'corrupted.json')
        
        # Create a corrupted JSON file
        with open(metrics_file, 'w') as f:
            f.write('{"invalid json": ')
        
        # Should return initialized structure, not crash
        collector = MetricsCollector(metrics_file)
        collector.start_run()
        collector.end_run(0)
        collector.save_metrics()
        
        # Verify it overwrote the corrupted file with valid data
        with open(metrics_file, 'r') as f:
            data = json.load(f)
        
        assert 'summary' in data
        assert data['summary']['total_runs'] == 1
    
    def test_update_summary_with_failed_exit_code(self, temp_dir):
        """Test _update_summary with exit code 2 (failure)."""
        metrics_file = str(Path(temp_dir) / 'metrics.json')
        collector = MetricsCollector(metrics_file)
        
        collector.start_run()
        collector.add_library_result('Movies', False, 10, 100, 10.0, 'Major error')
        collector.end_run(2)  # Exit code 2 = failure
        collector.save_metrics()
        
        with open(metrics_file, 'r') as f:
            data = json.load(f)
        
        assert data['summary']['total_runs'] == 1
        assert data['summary']['successful_runs'] == 0
        assert data['summary']['partial_runs'] == 0
        assert data['summary']['failed_runs'] == 1
    
    def test_get_current_metrics(self, temp_dir):
        """Test get_current_metrics returns a copy of current run data."""
        metrics_file = str(Path(temp_dir) / 'metrics.json')
        collector = MetricsCollector(metrics_file)
        
        collector.start_run()
        collector.add_library_result('Movies', True, 100, 95, 105.26)
        
        current = collector.get_current_metrics()
        
        # Verify it's a copy
        assert current == collector.current_run
        assert current is not collector.current_run
        
        # Modifying the copy shouldn't affect the original
        current['libraries_total'] = 999
        assert collector.current_run['libraries_total'] == 1
    
    def test_load_latest_metrics_corrupted_json(self, temp_dir):
        """Test load_latest_metrics with corrupted JSON file."""
        metrics_file = str(Path(temp_dir) / 'corrupted2.json')
        
        # Create a corrupted JSON file
        with open(metrics_file, 'w') as f:
            f.write('not valid json at all')
        
        # Should return None instead of crashing
        result = MetricsCollector.load_latest_metrics(metrics_file)
        
        assert result is None
