import os
import tempfile
import shutil
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
import uuid

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod
from magic_pdf.data.read_api import read_local_images

# 加载 .env 文件
load_dotenv()

app = FastAPI(
    title="MinerU API 服务",
    description="简化版 MinerU API 服务，支持 PDF 和图片处理",
    version="2.0.0",
    root_path="/mineru"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bearer Token 配置 - 从 .env 文件读取
BEARER_TOKEN = os.getenv("API_TOKEN", "your-secret-token-here")
if BEARER_TOKEN == "your-secret-token-here":
    print("⚠️  警告: 正在使用默认 API Token，请在 .env 文件中设置 API_TOKEN")
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证 Bearer Token"""
    if credentials.credentials != BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# 响应模型
class ProcessResponse(BaseModel):
    success: bool
    markdown_content: str
    images: Optional[List[Dict[str, str]]] = None
    message: str

def encode_image_to_base64(image_path: str) -> str:
    """将图片文件编码为 base64 字符串"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"编码图片失败 {image_path}: {e}")
        return ""

def collect_images_from_dir(image_dir: str) -> List[Dict[str, str]]:
    """收集目录中的所有图片文件并编码为 base64"""
    images = []
    if not os.path.exists(image_dir):
        return images
    
    supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp']
    
    for filename in os.listdir(image_dir):
        file_path = os.path.join(image_dir, filename)
        if os.path.isfile(file_path):
            file_ext = Path(filename).suffix.lower()
            if file_ext in supported_formats:
                base64_content = encode_image_to_base64(file_path)
                if base64_content:
                    images.append({
                        "filename": filename,
                        "content": base64_content,
                        "format": file_ext.lstrip('.')
                    })
    
    return images

def process_pdf_document(file_path: str, return_images: bool = False) -> ProcessResponse:
    """处理 PDF 文档"""
    try:
        # 创建临时输出目录
        temp_output_dir = tempfile.mkdtemp(prefix="mineru_pdf_")
        local_image_dir = os.path.join(temp_output_dir, "images")
        local_md_dir = temp_output_dir
        
        os.makedirs(local_image_dir, exist_ok=True)
        
        image_dir = os.path.basename(local_image_dir)
        
        # 创建数据写入器
        image_writer = FileBasedDataWriter(local_image_dir)
        
        # PDF 处理
        reader = FileBasedDataReader("")
        pdf_bytes = reader.read(file_path)
        
        ds = PymuDocDataset(pdf_bytes)
        
        if ds.classify() == SupportedPdfParseMethod.OCR:
            infer_result = ds.apply(doc_analyze, ocr=True)
            pipe_result = infer_result.pipe_ocr_mode(image_writer)
        else:
            infer_result = ds.apply(doc_analyze, ocr=False)
            pipe_result = infer_result.pipe_txt_mode(image_writer)
        
        # 获取 Markdown 内容
        md_content = pipe_result.get_markdown(image_dir)
        
        # 收集图片文件（如果需要）
        images = None
        if return_images:
            images = collect_images_from_dir(local_image_dir)
        
        # 清理临时目录
        shutil.rmtree(temp_output_dir, ignore_errors=True)
        
        return ProcessResponse(
            success=True,
            markdown_content=md_content,
            images=images,
            message="PDF 处理完成"
        )
        
    except Exception as e:
        # 清理临时目录
        if 'temp_output_dir' in locals():
            shutil.rmtree(temp_output_dir, ignore_errors=True)
        
        return ProcessResponse(
            success=False,
            markdown_content="",
            images=None,
            message=f"PDF 处理失败: {str(e)}"
        )

def process_image_document(file_path: str, return_images: bool = False) -> ProcessResponse:
    """处理图片文档"""
    try:
        # 创建临时输出目录
        temp_output_dir = tempfile.mkdtemp(prefix="mineru_image_")
        local_image_dir = os.path.join(temp_output_dir, "images")
        
        os.makedirs(local_image_dir, exist_ok=True)
        
        image_dir = os.path.basename(local_image_dir)
        
        # 创建数据写入器
        image_writer = FileBasedDataWriter(local_image_dir)
        
        # 图片处理
        ds = read_local_images(file_path)[0]
        infer_result = ds.apply(doc_analyze, ocr=True)
        pipe_result = infer_result.pipe_ocr_mode(image_writer)
        
        # 获取 Markdown 内容
        md_content = pipe_result.get_markdown(image_dir)
        
        # 收集图片文件（如果需要）
        images = None
        if return_images:
            images = collect_images_from_dir(local_image_dir)
        
        # 清理临时目录
        shutil.rmtree(temp_output_dir, ignore_errors=True)
        
        return ProcessResponse(
            success=True,
            markdown_content=md_content,
            images=images,
            message="图片处理完成"
        )
        
    except Exception as e:
        # 清理临时目录
        if 'temp_output_dir' in locals():
            shutil.rmtree(temp_output_dir, ignore_errors=True)
        
        return ProcessResponse(
            success=False,
            markdown_content="",
            images=None,
            message=f"图片处理失败: {str(e)}"
        )

@app.post("/process/pdf", response_model=ProcessResponse)
async def process_pdf(
    file: UploadFile = File(...),
    return_images: bool = Form(False),
    token: str = Depends(verify_token)
):
    """
    处理 PDF 文件
    
    参数:
    - file: PDF 文件
    - return_images: 是否返回提取的图片文件 (base64 编码)，默认 False
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")
    
    # 保存上传的文件
    temp_file_path = None
    try:
        temp_file_path = os.path.join("/tmp", f"{uuid.uuid4()}_{file.filename}")
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 处理文档
        result = process_pdf_document(temp_file_path, return_images)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
    
    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/process/image", response_model=ProcessResponse)
async def process_image(
    file: UploadFile = File(...),
    return_images: bool = Form(False),
    token: str = Depends(verify_token)
):
    """
    处理图片文件
    
    参数:
    - file: 图片文件 (支持 jpg, jpeg, png, bmp, tiff, webp)
    - return_images: 是否返回处理后的图片文件 (base64 编码)，默认 False
    """
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"只支持以下格式: {', '.join(allowed_extensions)}"
        )
    
    # 保存上传的文件
    temp_file_path = None
    try:
        temp_file_path = os.path.join("/tmp", f"{uuid.uuid4()}_{file.filename}")
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 处理文档
        result = process_image_document(temp_file_path, return_images)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
    
    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/")
async def root():
    """API 根路径"""
    return {
        "message": "MinerU API 服务 v2.0",
        "description": "简化版 API，支持 PDF 和图片处理",
        "endpoints": {
            "process_pdf": "POST /process/pdf",
            "process_image": "POST /process/image"
        },
        "authentication": "Bearer Token 认证",
        "port": 8766
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "MinerU API"}

if __name__ == "__main__":
    import uvicorn
    import logging
    
    # 配置日志格式，包含时间信息
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    print("=" * 50)
    print("MinerU API 服务 v2.0")
    print("端口: 8766")
    print("认证: Bearer Token")
    print(f"Token: {BEARER_TOKEN}")
    print("=" * 50)
    
    # 配置 uvicorn 日志格式
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["default"],
        },
    }
    
    uvicorn.run(app, host="0.0.0.0", port=8766, log_config=log_config) 