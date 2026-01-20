"""Metrics collection and persistence for observability."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class MetricsCollector:
    """Collects and persists application metrics."""
    
    def __init__(self, metrics_file: str = 'data/metrics.json'):
        """Initialize metrics collector.
        
        Args:
            metrics_file: Path to metrics file for persistence.
        """
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.current_run = {
            'start_time': None,
            'end_time': None,
            'duration_seconds': None,
            'exit_code': None,
            'libraries_total': 0,
            'libraries_successful': 0,
            'libraries_failed': 0,
            'library_details': []
        }
    
    def start_run(self) -> None:
        """Mark the start of a processing run."""
        self.current_run['start_time'] = datetime.now(timezone.utc).isoformat()
    
    def end_run(self, exit_code: int) -> None:
        """Mark the end of a processing run.
        
        Args:
            exit_code: Exit code of the run (0=success, 1=partial, 2=failure).
        """
        end_time = datetime.now(timezone.utc)
        self.current_run['end_time'] = end_time.isoformat()
        self.current_run['exit_code'] = exit_code
        
        # Calculate duration
        if self.current_run['start_time']:
            start_time = datetime.fromisoformat(self.current_run['start_time'])
            duration = (end_time - start_time).total_seconds()
            self.current_run['duration_seconds'] = round(duration, 2)
    
    def add_library_result(
        self,
        name: str,
        success: bool,
        file_count: int,
        media_count: int,
        threshold_percentage: float,
        error_message: Optional[str] = None
    ) -> None:
        """Record the result of processing a library.
        
        Args:
            name: Library name.
            success: Whether processing was successful.
            file_count: Number of files found.
            media_count: Number of media items in Plex.
            threshold_percentage: Actual percentage of files vs media.
            error_message: Optional error message if failed.
        """
        self.current_run['libraries_total'] += 1
        if success:
            self.current_run['libraries_successful'] += 1
        else:
            self.current_run['libraries_failed'] += 1
        
        self.current_run['library_details'].append({
            'name': name,
            'success': success,
            'file_count': file_count,
            'media_count': media_count,
            'threshold_percentage': round(threshold_percentage, 2),
            'error_message': error_message
        })
    
    def save_metrics(self) -> None:
        """Persist metrics to file and update historical data."""
        # Load existing metrics
        historical_metrics = self._load_historical_metrics()
        
        # Add current run to history
        historical_metrics['runs'].append(self.current_run)
        
        # Update summary statistics
        self._update_summary(historical_metrics)
        
        # Write to file
        with open(self.metrics_file, 'w') as f:
            json.dump(historical_metrics, f, indent=2)
    
    def _load_historical_metrics(self) -> Dict:
        """Load existing metrics or initialize new structure."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return {
            'last_updated': None,
            'summary': {
                'total_runs': 0,
                'successful_runs': 0,
                'partial_runs': 0,
                'failed_runs': 0,
                'total_libraries_processed': 0,
                'total_libraries_succeeded': 0,
                'total_libraries_failed': 0
            },
            'runs': []
        }
    
    def _update_summary(self, metrics: Dict) -> None:
        """Update summary statistics.
        
        Args:
            metrics: Metrics dictionary to update.
        """
        metrics['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Count run outcomes
        exit_code = self.current_run['exit_code']
        metrics['summary']['total_runs'] += 1
        
        if exit_code == 0:
            metrics['summary']['successful_runs'] += 1
        elif exit_code == 1:
            metrics['summary']['partial_runs'] += 1
        else:
            metrics['summary']['failed_runs'] += 1
        
        # Update library statistics
        metrics['summary']['total_libraries_processed'] += self.current_run['libraries_total']
        metrics['summary']['total_libraries_succeeded'] += self.current_run['libraries_successful']
        metrics['summary']['total_libraries_failed'] += self.current_run['libraries_failed']
        
        # Keep only last 100 runs to prevent file from growing too large
        if len(metrics['runs']) > 100:
            metrics['runs'] = metrics['runs'][-100:]
    
    def get_current_metrics(self) -> Dict:
        """Get current run metrics.
        
        Returns:
            Dictionary of current metrics.
        """
        return self.current_run.copy()
    
    @staticmethod
    def load_latest_metrics(metrics_file: str = 'data/metrics.json') -> Optional[Dict]:
        """Load the latest metrics from file.
        
        Args:
            metrics_file: Path to metrics file.
            
        Returns:
            Latest metrics dictionary or None if file doesn't exist.
        """
        path = Path(metrics_file)
        if not path.exists():
            return None
        
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
