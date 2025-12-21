"""
Centralized Logging Module for AWS WAF Scanner Enterprise
=========================================================
Provides consistent logging across all modules with file and console output.

Usage:
    from logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Message")
    logger.error("Error message", exc_info=True)
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path
import json as json_module

# ============================================================================
# CONFIGURATION
# ============================================================================

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
LOG_DIR = os.environ.get('LOG_DIR', 'logs')
LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_FILE_BACKUP_COUNT = 5
LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# ============================================================================
# CUSTOM FORMATTERS
# ============================================================================

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[41m',   # Red background
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
            
        return json_module.dumps(log_data)


# ============================================================================
# LOGGER FACTORY
# ============================================================================

_loggers = {}

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger with consistent configuration.
    
    Args:
        name: Logger name (typically __name__)
        level: Optional override for log level
        
    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    log_level = getattr(logging, level or LOG_LEVEL, logging.INFO)
    logger.setLevel(log_level)
    
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if sys.stdout.isatty():
        console_handler.setFormatter(ColoredFormatter(LOG_FORMAT, LOG_DATE_FORMAT))
    else:
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    
    logger.addHandler(console_handler)
    
    # File handler (rotating)
    try:
        Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
        log_file = os.path.join(LOG_DIR, 'waf_scanner.log')
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=LOG_FILE_MAX_BYTES,
            backupCount=LOG_FILE_BACKUP_COUNT
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        logger.addHandler(file_handler)
    except (OSError, PermissionError):
        pass
    
    logger.propagate = False
    _loggers[name] = logger
    return logger


def log_exception(logger: logging.Logger, message: str, exc: Exception, **extra):
    """Log an exception with full traceback"""
    extra_str = ' | '.join(f"{k}={v}" for k, v in extra.items()) if extra else ''
    full_message = f"{message} | {extra_str}" if extra_str else message
    logger.error(full_message, exc_info=exc)


def log_aws_operation(logger: logging.Logger, operation: str, service: str, 
                      region: str = None, account_id: str = None):
    """Log an AWS operation with standard context"""
    context = f"service={service}, operation={operation}"
    if region:
        context += f", region={region}"
    if account_id:
        context += f", account={account_id}"
    logger.debug(f"AWS API Call: {context}")


def log_performance(logger: logging.Logger, operation: str, duration_seconds: float):
    """Log performance metrics"""
    logger.info(f"Performance: {operation} completed in {duration_seconds:.3f}s")


# Create default application logger
app_logger = get_logger('waf_scanner')

__all__ = ['get_logger', 'log_exception', 'log_aws_operation', 'log_performance', 'app_logger']
