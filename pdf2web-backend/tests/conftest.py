"""Pytest configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def temp_upload_dir():
    """Create temporary upload directory."""
    temp_dir = Path(tempfile.mkdtemp())
    original_upload_dir = settings.upload_dir
    settings.upload_dir = temp_dir
    yield temp_dir
    settings.upload_dir = original_upload_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_pdf_content():
    """Generate minimal valid PDF content for testing."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
