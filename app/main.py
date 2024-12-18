from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
import os
from PIL import Image, ImageEnhance
import io
import numpy as np
from pathlib import Path
import config
import cv2

app = FastAPI()

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))

# 确保上传目录存在
UPLOAD_DIR = config.UPLOAD_DIR
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, detail="File must be an image")
    
    content = await file.read()
    image = Image.open(io.BytesIO(content))
    
    # 保存原始图片
    filename = f"{file.filename}"
    filepath = UPLOAD_DIR / filename
    image.save(filepath)
    
    return {"filename": filename}

@app.post("/crop")
async def crop_image(
    file: UploadFile = File(...),
    x: int = 0,
    y: int = 0,
    width: int = 100,
    height: int = 100
):
    content = await file.read()
    image = Image.open(io.BytesIO(content))
    
    # 裁剪图片
    cropped_image = image.crop((x, y, x + width, y + height))
    
    # 保存裁剪后的图片
    output = io.BytesIO()
    cropped_image.save(output, format=image.format)
    output.seek(0)
    
    filename = f"cropped_{file.filename}"
    filepath = UPLOAD_DIR / filename
    cropped_image.save(filepath)
    
    return {"filename": filename}

@app.post("/remove-watermark")
async def remove_watermark(file: UploadFile = File(...)):
    try:
        # 确保上传目录存在
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        
        # 转换为numpy数组
        img_array = np.array(image)
        
        # 转换为OpenCV格式
        if len(img_array.shape) == 3:
            # 保存原始图像副本
            original_img = img_array.copy()
            
            # 转换为灰度图
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # 自适应阈值处理
            binary = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 25, 15
            )
            
            # 使用形态学操作找到可能的水印区域
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            # 找到连通区域
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
            
            # 创建水印蒙版
            mask = np.zeros_like(gray)
            
            # 分析每个连通区域
            for i in range(1, num_labels):  # 跳过背景（i=0）
                area = stats[i, cv2.CC_STAT_AREA]
                if area > 100 and area < gray.size * 0.3:  # 根据区域大小筛选
                    mask[labels == i] = 255
            
            # 扩展蒙版区域
            mask = cv2.dilate(mask, kernel, iterations=2)
            
            # 对每个颜色通道分别进行修复
            result = np.zeros_like(original_img)
            for i in range(3):
                result[:,:,i] = cv2.inpaint(
                    original_img[:,:,i],
                    mask,
                    3,
                    cv2.INPAINT_NS  # 使用 NS 方法，效果更自然
                )
            
            # 将结果与原图混合，使过渡更自然
            alpha = 0.8
            img_array = cv2.addWeighted(result, alpha, original_img, 1-alpha, 0)
            
            # 轻微的锐化
            kernel_sharpen = np.array([[-1,-1,-1],
                                     [-1, 9,-1],
                                     [-1,-1,-1]])
            img_array = cv2.filter2D(img_array, -1, kernel_sharpen)
        
        # 转回PIL图像
        processed_image = Image.fromarray(img_array)
        
        # 保存处理后的图片
        filename = f"nowatermark_{file.filename}"
        filepath = UPLOAD_DIR / filename
        
        # 确保文件扩展名正确
        if not filepath.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            filepath = filepath.with_suffix('.png')
        
        # 保存图片
        processed_image.save(str(filepath), quality=95)  # 使用str()确保路径格式正确
        
        # 验证文件是否成功保存
        if not filepath.exists():
            raise HTTPException(status_code=500, detail="Failed to save processed image")
        
        return {"filename": filepath.name}
        
    except Exception as e:
        print(f"Error in remove_watermark: {str(e)}")  # 添加日志
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stitch")
async def stitch_images(files: list[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(400, detail="Need at least 2 images to stitch")
    
    images = []
    for file in files:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        images.append(img)
    
    # 获取所有图片的宽度和最大高度
    total_width = sum(img.width for img in images)
    max_height = max(img.height for img in images)
    
    # 创建新图片
    stitched = Image.new('RGB', (total_width, max_height))
    
    # 拼接图片
    x_offset = 0
    for img in images:
        stitched.paste(img, (x_offset, 0))
        x_offset += img.width
    
    # 保存拼接后的图片
    filename = "stitched_image.jpg"
    filepath = UPLOAD_DIR / filename
    stitched.save(filepath)
    
    return {"filename": filename}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT, reload=config.DEBUG)
