from pathlib import Path
import logging
import shutil
import sys
from typing import Optional

class LoggingManager:
    """Manages logging configuration for both production and test environments"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.production_format = "%(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            self.test_format = "%(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            self.log_level = logging.DEBUG
            self.test_logs_dir = Path(__file__).parent.parent / "test" / "test_logs"
            self._initialized = True
            self.test_logs_dir.mkdir(parents=True, exist_ok=True)

    def setup_production_logging(self):
        """Configure logging for production environment"""
        # Clear any existing handlers
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
            
        # Configure production logging
        logging.basicConfig(
            level=self.log_level,
            format=self.production_format,
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        
        logging.info("Production logging configured")

    def setup_test_logging(self, test_name: str) -> logging.Logger:
        """Configure logging for test environment with proper file handling"""
        # Ensure test logs directory exists
        self.test_logs_dir.mkdir(exist_ok=True)
        
        # Create module-specific log file
        module_name = test_name.split('.')[-1] if '.' in test_name else test_name
        log_file = self.test_logs_dir / f"{module_name}.log"
        
        # Create and configure file handler
        file_handler = logging.FileHandler(log_file, mode='a')  # Append mode
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(logging.Formatter(self.test_format))
        
        # Get or create logger
        logger = logging.getLogger(module_name)
        logger.setLevel(self.log_level)
        
        # Remove any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            
        # Add file handler
        logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        logger.info(f"Test logging configured for {module_name}")
        return logger

    def cleanup_test_logging(self, logger: logging.Logger):
        """Clean up test logging configuration"""
        for handler in logger.handlers[:]:
            handler.flush()
            handler.close()
            logger.removeHandler(handler)
            
    def cleanup_test_directory(self):
        """Clean up test logs directory between test runs"""
        if self.test_logs_dir.exists():
            shutil.rmtree(self.test_logs_dir)
        self.test_logs_dir.mkdir(exist_ok=True)

# Singleton instance
logging_manager = LoggingManager()