import os
from pathlib import Path

# 基础配置
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
TEMPLATES_DIR = BASE_DIR / "templates"

# 服务器配置
HOST = os.getenv("APP_HOST", "0.0.0.0")
PORT = int(os.getenv("APP_PORT", "8000"))
DEBUG = os.getenv("APP_DEBUG", "False").lower() == "true"

# 上传文件配置
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}

# 创建必要的目录
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
