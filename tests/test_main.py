import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io
import os
from pathlib import Path

def create_test_image(path: Path, size=(100, 100), color='white'):
    """Helper function to create a test image"""
    img = Image.new('RGB', size, color)
    img.save(path)
    return img

def test_read_root(client):
    """Test the root endpoint returns the index page"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

@pytest.mark.asyncio
async def test_upload_image(client, test_image_path):
    """Test image upload endpoint"""
    # Create a test image
    create_test_image(test_image_path)
    
    # Upload the image
    with open(test_image_path, "rb") as f:
        files = {"file": ("test_image.png", f, "image/png")}
        response = client.post("/upload", files=files)
    
    assert response.status_code == 200
    assert "filename" in response.json()
    assert response.json()["filename"] == "test_image.png"

@pytest.mark.asyncio
async def test_crop_image(client, test_image_path):
    """Test image cropping endpoint"""
    # Create a test image
    create_test_image(test_image_path, size=(200, 200))
    
    # Test cropping parameters
    crop_params = {
        "x": 0,
        "y": 0,
        "width": 100,
        "height": 100
    }
    
    with open(test_image_path, "rb") as f:
        files = {"file": ("test_image.png", f, "image/png")}
        response = client.post("/crop", files=files, data=crop_params)
    
    assert response.status_code == 200
    assert "filename" in response.json()
    
    # Verify the cropped image dimensions
    cropped_path = Path("app/static/uploads") / response.json()["filename"]
    with Image.open(cropped_path) as img:
        assert img.size == (100, 100)

@pytest.mark.asyncio
async def test_remove_watermark(client, test_watermark_image_path):
    """Test watermark removal endpoint"""
    # Create a test image with a white background and gray watermark
    img = Image.new('RGB', (200, 200), 'white')
    # Add a gray rectangle as watermark
    for x in range(50, 150):
        for y in range(50, 150):
            img.putpixel((x, y), (200, 200, 200))
    img.save(test_watermark_image_path)
    
    with open(test_watermark_image_path, "rb") as f:
        files = {"file": ("test_watermark.png", f, "image/png")}
        response = client.post("/remove-watermark", files=files)
    
    assert response.status_code == 200
    assert "filename" in response.json()
    
    # Verify the watermark has been processed
    processed_path = Path("app/static/uploads") / response.json()["filename"]
    assert processed_path.exists()

@pytest.mark.asyncio
async def test_stitch_images(client, test_images_for_stitch):
    """Test image stitching endpoint"""
    # Create two test images
    create_test_image(test_images_for_stitch[0], size=(100, 100), color='red')
    create_test_image(test_images_for_stitch[1], size=(100, 100), color='blue')
    
    # Upload both images
    files = []
    opened_files = []
    for path in test_images_for_stitch:
        f = open(path, "rb")
        opened_files.append(f)
        files.append(("files", (path.name, f, "image/png")))
            
    try:
        response = client.post("/stitch", files=files)
        assert response.status_code == 200
        assert "filename" in response.json()
        
        # Verify the stitched image
        stitched_path = Path("app/static/uploads") / response.json()["filename"]
        with Image.open(stitched_path) as img:
            # The width should be the sum of individual widths
            assert img.size == (200, 100)
    finally:
        # Close all opened files
        for f in opened_files:
            f.close()

@pytest.mark.asyncio
async def test_rotate_image(client, test_image_path):
    # 准备测试数据
    with open(test_image_path, "rb") as f:
        content = f.read()
        
    files = {"file": ("test_image.png", content, "image/png")}
    data = {
        "angle": "90.0",  # 作为字符串发送
        "bg_color": "#FFFFFF"
    }
    
    # 发送请求
    response = client.post("/rotate", files=files, data=data)
    assert response.status_code == 200
    
    response_data = response.json()
    assert "filename" in response_data
    assert response_data["filename"].startswith("rotated_")

@pytest.mark.asyncio
async def test_rotate_image_invalid_angle(client, test_image_path):
    # 准备测试数据
    with open(test_image_path, "rb") as f:
        content = f.read()
        
    files = {"file": ("test_image.png", content, "image/png")}
    data = {
        "angle": "invalid",  # 无效角度
        "bg_color": "#FFFFFF"
    }
    
    # 发送请求
    response = client.post("/rotate", files=files, data=data)
    assert response.status_code == 400  # 应该返回 400 Bad Request
    
    response_data = response.json()
    assert "Invalid angle format" in response_data["detail"]

@pytest.mark.asyncio
async def test_rotate_image_invalid_color(client, test_image_path):
    # 准备测试数据
    with open(test_image_path, "rb") as f:
        content = f.read()
        
    files = {"file": ("test_image.png", content, "image/png")}
    data = {
        "angle": "90.0",
        "bg_color": "invalid"  # 无效颜色
    }
    
    # 发送请求
    response = client.post("/rotate", files=files, data=data)
    assert response.status_code == 400  # 应该返回 400 Bad Request
    
    response_data = response.json()
    assert "Invalid background color format" in response_data["detail"]

@pytest.mark.asyncio
async def test_invalid_crop_parameters(client, test_image_path):
    """Test cropping with invalid parameters"""
    create_test_image(test_image_path)
    
    # Test with negative coordinates
    crop_params = {
        "x": -10,
        "y": -10,
        "width": 100,
        "height": 100
    }
    
    with open(test_image_path, "rb") as f:
        files = {"file": ("test_image.png", f, "image/png")}
        response = client.post("/crop", files=files, data=crop_params)
    
    assert response.status_code == 200  # The API will handle invalid coordinates

def test_invalid_image_upload(client):
    """Test uploading invalid file type"""
    # Create a text file instead of an image
    invalid_file = io.BytesIO(b"This is not an image")
    files = {"file": ("test.txt", invalid_file, "text/plain")}
    
    response = client.post("/upload", files=files)
    assert response.status_code == 400
