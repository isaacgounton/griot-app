"""
Enhanced logging configuration using loguru for rich structured logging.

This module replaces standard Python logging with loguru for better performance,
richer output, and enhanced debugging capabilities.
"""
import sys
import os
from typing import Any, Optional
from loguru import logger
from pathlib import Path

class LoggingConfig:
    """Enhanced logging configuration with context-aware structured logging."""
    
    def _get_log_format(self) -> str:
        """Get appropriate log format based on environment."""
        if os.getenv("ENVIRONMENT") == "production":
            # JSON format for production logging
            return "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message} | {extra}"
        else:
            # Rich format for development
            return "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> | <blue>{extra}</blue>"
    
    def __init__(self):
        self.is_configured = False
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_format = self._get_log_format()
    
    def configure_logging(self):
        """Configure loguru logging with enhanced features."""
        if self.is_configured:
            return
            
        # Remove default logger
        logger.remove()
        
        # Add console handler with rich formatting
        logger.add(
            sys.stdout,
            colorize=True,
            format=self.log_format,
            level=self.log_level,
            backtrace=True,
            diagnose=True,
            enqueue=True  # Thread-safe logging
        )
        
        # Add file handler for errors
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logger.add(
            log_dir / "error.log",
            format=self.log_format,
            level="ERROR",
            rotation="10 MB",
            retention="30 days",
            backtrace=True,
            diagnose=True,
            enqueue=True
        )
        
        # Add file handler for all logs
        logger.add(
            log_dir / "app.log",
            format=self.log_format,
            level=self.log_level,
            rotation="50 MB",
            retention="7 days",
            backtrace=True,
            diagnose=True,
            enqueue=True
        )
        
        self.is_configured = True
        logger.info("Enhanced loguru logging configured successfully")
        
    def get_context_logger(self, **context: Any):
        """Get a logger with bound context for structured logging."""
        return logger.bind(**context)
        
    def log_operation_start(self, operation: str, **context: Any):
        """Log the start of an operation with context."""
        context_logger = self.get_context_logger(operation=operation, **context)
        context_logger.info(f"Starting {operation}")
        return context_logger
        
    def log_operation_complete(self, operation: str, duration: Optional[float] = None, **context: Any):
        """Log the completion of an operation with timing."""
        context_logger = self.get_context_logger(
            operation=operation, 
            duration_seconds=duration,
            **context
        )
        if duration:
            context_logger.info(f"Completed {operation} in {duration:.2f}s")
        else:
            context_logger.info(f"Completed {operation}")
        return context_logger
        
    def log_operation_error(self, operation: str, error: Exception, **context: Any):
        """Log an operation error with full context."""
        context_logger = self.get_context_logger(
            operation=operation,
            error_type=type(error).__name__,
            error_message=str(error),
            **context
        )
        context_logger.error(f"Failed {operation}: {error}")
        return context_logger

# Global logging configuration instance
logging_config = LoggingConfig()

# Convenience functions for easy access
def get_logger(**context: Any):
    """Get a context-aware logger instance."""
    return logging_config.get_context_logger(**context)

def log_operation_start(operation: str, **context: Any):
    """Log operation start with context."""
    return logging_config.log_operation_start(operation, **context)

def log_operation_complete(operation: str, duration: Optional[float] = None, **context: Any):
    """Log operation completion with timing."""
    return logging_config.log_operation_complete(operation, duration, **context)

def log_operation_error(operation: str, error: Exception, **context: Any):
    """Log operation error with full context."""
    return logging_config.log_operation_error(operation, error, **context)

def configure_enhanced_logging():
    """Initialize enhanced logging system."""
    logging_config.configure_logging()