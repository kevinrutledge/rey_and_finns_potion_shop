import os
os.environ['TESTING'] = 'true'

import pytest
from pathlib import Path
from src.logging_config import logging_manager

@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Ensure we're in test environment"""
    yield
    os.environ.pop('TESTING', None)

@pytest.fixture(scope="session", autouse=True)
def test_logs_setup():
    """Setup and cleanup test logs directory at session level"""
    test_dir = Path(__file__).parent / "test_logs"
    test_dir.mkdir(parents=True, exist_ok=True)
    logging_manager.cleanup_test_directory()
    yield

@pytest.fixture
def test_logger(request):
    """Provide test-specific logger"""
    module_name = request.module.__name__
    logger = logging_manager.setup_test_logging(module_name)
    
    yield logger
    
    logging_manager.cleanup_test_logging(logger)
