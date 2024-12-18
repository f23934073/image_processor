import pytest
from fastapi.testclient import TestClient
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_path = str(Path(__file__).parent.parent / "app")
if app_path not in sys.path:
    sys.path.append(app_path)

from main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_image_path():
    """Fixture to provide path to test image"""
    return Path(__file__).parent / "test_images" / "test_image.png"

@pytest.fixture
def test_watermark_image_path():
    """Fixture to provide path to test watermark image"""
    return Path(__file__).parent / "test_images" / "test_watermark.png"

@pytest.fixture
def test_images_for_stitch():
    """Fixture to provide paths to test images for stitching"""
    test_images_dir = Path(__file__).parent / "test_images"
    return [
        test_images_dir / "stitch_1.png",
        test_images_dir / "stitch_2.png"
    ]

@pytest.fixture(autouse=True)
def setup_and_cleanup():
    """Fixture to setup and cleanup test environment"""
    # Setup: Create uploads directory if it doesn't exist
    upload_dir = Path(__file__).parent.parent / "app" / "static" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Cleanup: Remove all files in uploads directory after each test
    for file in upload_dir.glob("*"):
        if file.is_file():
            file.unlink()
