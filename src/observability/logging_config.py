"""Logging configuration with structured output and rotation support."""

import logging
import logging.handlers
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


VALID_LOG_FORMATS = {'standard', 'json'}


def _normalize_log_level(log_level: str) -> tuple[int, bool]:
    """Normalize a log level string and report whether it was valid."""
    normalized_level = str(log_level).strip().upper()
    level_value = logging.getLevelName(normalized_level)
    if isinstance(level_value, int):
        return level_value, True
    return logging.INFO, False


def _normalize_log_format(log_format: str) -> tuple[str, bool]:
    """Normalize a log format string and report whether it was valid."""
    normalized_format = str(log_format).strip().lower()
    if normalized_format in VALID_LOG_FORMATS:
        return normalized_format, True
    return 'standard', False


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: Log record to format.
            
        Returns:
            JSON-formatted log string.
        """
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'library_name'):
            log_data['library_name'] = record.library_name
        if hasattr(record, 'file_count'):
            log_data['file_count'] = record.file_count
        if hasattr(record, 'media_count'):
            log_data['media_count'] = record.media_count
        
        return json.dumps(log_data)


def setup_logging(
    log_level: str = 'INFO',
    log_format: str = 'standard',
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """Configure logging with optional rotation and structured formatting.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Format style ('standard' or 'json').
        log_file: Optional file path for file-based logging with rotation.
        max_bytes: Maximum size of log file before rotation (default: 10MB).
        backup_count: Number of backup log files to keep (default: 5).
        
    Returns:
        Configured root logger.
    """
    # Get root logger
    logger = logging.getLogger()
    normalized_level, is_valid_level = _normalize_log_level(log_level)
    normalized_format, is_valid_format = _normalize_log_format(log_format)

    logger.setLevel(normalized_level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Choose formatter
    if normalized_format == 'json':
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler (always to stdout for Docker)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Optional file handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if not is_valid_level:
        logger.warning('Invalid log level "%s" provided. Falling back to INFO.', log_level)
    if not is_valid_format:
        logger.warning('Invalid log format "%s" provided. Falling back to standard.', log_format)
    
    return logger
