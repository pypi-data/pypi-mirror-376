"""
文件上传路由
"""
import logging
from typing import List
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from models import (
    FileCheckRequest, ChunkUploadRequest, FileMergeRequest, 
    FileUploadResponse, FileInfo
)
from services import file_upload_service
from config import settings

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["文件上传"])


@router.post("/check", response_model=FileUploadResponse, summary="检查文件上传状态")
async def check_file_status(request: FileCheckRequest):
    """
    检查文件上传状态，支持断点续传
    
    - **file_id**: 文件唯一标识符
    - **file_name**: 原始文件名
    - **file_size**: 文件总大小(字节)
    - **total_chunks**: 分片总数
    - **file_md5**: 文件MD5值(可选)
    """
    try:
        # 检查文件大小限制
        if request.file_size > settings.max_file_size:
            return FileUploadResponse.error(
                code=400,
                message=f"文件大小超过限制，最大允许 {settings.max_file_size / (1024**3):.1f}GB"
            )
        
        # 检查文件类型
        if settings.allowed_file_types:
            file_ext = request.file_name.split('.')[-1].lower()
            if file_ext not in settings.allowed_file_types:
                return FileUploadResponse.error(
                    code=400,
                    message=f"不支持的文件类型: {file_ext}"
                )
        
        file_info = await file_upload_service.check_file_status(
            file_id=request.file_id,
            file_name=request.file_name,
            file_size=request.file_size,
            total_chunks=request.total_chunks,
            dataset_name=request.dataset_name,
            file_md5=request.file_md5
        )
        
        return FileUploadResponse.success(
            message="文件状态检查成功",
            file_id=file_info.file_id,
            file_name=file_info.file_name,
            uploaded_chunks=file_info.uploaded_chunks,
            is_completed=file_info.is_completed,
            file_size=file_info.file_size,
            progress=file_info.progress
        )
        
    except Exception as e:
        logger.error(f"检查文件状态失败: {str(e)}")
        return FileUploadResponse.error(message=f"检查文件状态失败: {str(e)}")


@router.post("/chunk", response_model=FileUploadResponse, summary="上传文件分片")
async def upload_chunk(
    file_id: str = Form(..., description="文件唯一标识符"),
    file_name: str = Form(..., description="原始文件名"),
    file_size: int = Form(..., description="文件总大小"),
    chunk_index: int = Form(..., description="分片序号"),
    total_chunks: int = Form(..., description="分片总数"),
    chunk_size: int = Form(..., description="分片大小"),
    dataset_name: str = Form(..., description="数据集名称"),
    chunk_md5: str = Form(None, description="分片MD5值"),
    file_md5: str = Form(None, description="文件MD5值"),
    chunk_file: UploadFile = File(..., description="分片文件数据")
):
    """
    上传文件分片
    
    - **file_id**: 文件唯一标识符
    - **chunk_index**: 当前分片序号(从0开始)
    - **chunk_file**: 分片文件数据
    - 其他参数用于验证和记录
    """
    try:
        # 验证请求参数
        request = ChunkUploadRequest(
            file_id=file_id,
            file_name=file_name,
            file_size=file_size,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            chunk_size=chunk_size,
            dataset_name=dataset_name,
            chunk_md5=chunk_md5,
            file_md5=file_md5
        )
        
        # 读取分片数据
        chunk_data = await chunk_file.read()
        
        # 验证分片大小
        if len(chunk_data) != chunk_size:
            return FileUploadResponse.error(
                code=400,
                message=f"分片大小不匹配，期望: {chunk_size}, 实际: {len(chunk_data)}"
            )
        
        # 上传分片
        success = await file_upload_service.upload_chunk(
            file_id=file_id,
            chunk_index=chunk_index,
            chunk_data=chunk_data,
            chunk_md5=chunk_md5
        )
        
        if not success:
            return FileUploadResponse.error(message="分片上传失败")
        
        # 获取更新后的文件信息
        file_info = file_upload_service.get_file_info(file_id)
        if not file_info:
            return FileUploadResponse.error(message="获取文件信息失败")
        
        return FileUploadResponse.success(
            message=f"分片 {chunk_index} 上传成功",
            file_id=file_info.file_id,
            file_name=file_info.file_name,
            uploaded_chunks=file_info.uploaded_chunks,
            is_completed=file_info.is_completed,
            file_size=file_info.file_size,
            progress=file_info.progress
        )
        
    except ValueError as e:
        return FileUploadResponse.error(code=400, message=str(e))
    except Exception as e:
        logger.error(f"上传分片失败: {str(e)}")
        return FileUploadResponse.error(message=f"上传分片失败: {str(e)}")


@router.post("/merge", response_model=FileUploadResponse, summary="合并文件分片")
async def merge_chunks(request: FileMergeRequest):
    """
    合并文件分片，完成文件上传
    
    - **file_id**: 文件唯一标识符
    - **file_name**: 目标文件名
    - **total_chunks**: 分片总数
    - **file_md5**: 文件MD5值(可选，用于校验)
    """
    try:
        # 合并分片
        success, file_path = await file_upload_service.merge_chunks(
            file_id=request.file_id,
            target_filename=request.file_name,
            file_md5=request.file_md5
        )
        
        if not success:
            return FileUploadResponse.error(message="文件合并失败")
        
        # 构建文件访问URL
        file_url = f"/api/download/{request.file_name}"
        
        return FileUploadResponse.success(
            message="文件上传完成",
            file_id=request.file_id,
            file_name=request.file_name,
            file_url=file_url,
            is_completed=True,
            progress=100.0
        )
        
    except ValueError as e:
        return FileUploadResponse.error(code=400, message=str(e))
    except Exception as e:
        logger.error(f"合并文件失败: {str(e)}")
        return FileUploadResponse.error(message=f"合并文件失败: {str(e)}")


@router.get("/status/{file_id}", response_model=FileUploadResponse, summary="获取文件上传状态")
async def get_upload_status(file_id: str):
    """
    获取文件上传状态
    
    - **file_id**: 文件唯一标识符
    """
    try:
        file_info = file_upload_service.get_file_info(file_id)
        if not file_info:
            return FileUploadResponse.error(code=404, message="文件信息不存在")
        
        return FileUploadResponse.success(
            message="获取状态成功",
            file_id=file_info.file_id,
            file_name=file_info.file_name,
            uploaded_chunks=file_info.uploaded_chunks,
            is_completed=file_info.is_completed,
            file_size=file_info.file_size,
            progress=file_info.progress
        )
        
    except Exception as e:
        logger.error(f"获取文件状态失败: {str(e)}")
        return FileUploadResponse.error(message=f"获取文件状态失败: {str(e)}")


@router.delete("/{file_id}", response_model=FileUploadResponse, summary="取消文件上传")
async def cancel_upload(file_id: str, background_tasks: BackgroundTasks):
    """
    取消文件上传，清理临时文件
    
    - **file_id**: 文件唯一标识符
    """
    try:
        file_info = file_upload_service.get_file_info(file_id)
        if not file_info:
            return FileUploadResponse.error(code=404, message="文件信息不存在")
        
        # 异步清理临时文件
        background_tasks.add_task(file_upload_service._cleanup_temp_files, file_id)
        
        # 移除文件信息
        file_upload_service.remove_file_info(file_id)
        
        return FileUploadResponse.success(message="上传已取消，临时文件已清理")
        
    except Exception as e:
        logger.error(f"取消上传失败: {str(e)}")
        return FileUploadResponse.error(message=f"取消上传失败: {str(e)}")


# 下载路由
download_router = APIRouter(prefix="/api/download", tags=["文件下载"])


@download_router.get("/{filename}", summary="下载文件")
async def download_file(filename: str):
    """
    下载已上传的文件
    
    - **filename**: 文件名
    """
    import os
    file_path = os.path.join(settings.upload_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )
