"""
文件上传服务类
"""
import os
import json
import hashlib
import asyncio
import aiofiles
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from models import FileInfo, UploadStatus
from config import settings, get_dataset_upload_path, get_dataset_temp_path


class FileUploadService:
    """文件上传服务"""
    
    def __init__(self):
        self._file_registry: Dict[str, FileInfo] = {}
        self._upload_locks: Dict[str, asyncio.Lock] = {}
        
    async def check_file_status(self, file_id: str, file_name: str, file_size: int, 
                               total_chunks: int, dataset_name: str, 
                               file_md5: Optional[str] = None) -> FileInfo:
        """检查文件上传状态，支持断点续传"""
        
        # 如果文件信息已存在，返回现有信息
        if file_id in self._file_registry:
            file_info = self._file_registry[file_id]
            # 更新时间戳
            file_info.updated_at = datetime.now().isoformat()
            return file_info
        
        # 检查是否有已存在的分片文件
        temp_dir_path = get_dataset_temp_path(dataset_name)
        temp_dir = Path(temp_dir_path) / file_id
        uploaded_chunks = []
        
        if temp_dir.exists():
            for chunk_file in temp_dir.glob("chunk_*"):
                try:
                    chunk_index = int(chunk_file.name.split("_")[1])
                    uploaded_chunks.append(chunk_index)
                except (ValueError, IndexError):
                    continue
            uploaded_chunks.sort()
        
        # 创建新的文件信息
        file_info = FileInfo(
            file_id=file_id,
            file_name=file_name,
            file_size=file_size,
            file_md5=file_md5,
            total_chunks=total_chunks,
            uploaded_chunks=uploaded_chunks,
            status=UploadStatus.PENDING if not uploaded_chunks else UploadStatus.UPLOADING,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            dataset_name=dataset_name
        )
        
        # 检查是否已经完成上传
        if file_info.is_completed:
            upload_dir_path = get_dataset_upload_path(dataset_name)
            final_file_path = Path(upload_dir_path) / file_name
            if final_file_path.exists():
                file_info.status = UploadStatus.COMPLETED
                file_info.file_path = str(final_file_path)
        
        self._file_registry[file_id] = file_info
        return file_info
    
    async def upload_chunk(self, file_id: str, chunk_index: int, chunk_data: bytes,
                          chunk_md5: Optional[str] = None) -> bool:
        """上传单个分片"""
        
        # 获取或创建上传锁
        if file_id not in self._upload_locks:
            self._upload_locks[file_id] = asyncio.Lock()
        
        async with self._upload_locks[file_id]:
            # 检查文件信息是否存在
            if file_id not in self._file_registry:
                raise ValueError(f"文件 {file_id} 信息不存在，请先调用检查接口")
            
            file_info = self._file_registry[file_id]
            
            # 检查分片是否已经上传
            if chunk_index in file_info.uploaded_chunks:
                return True
            
            # 创建临时目录
            temp_dir_path = get_dataset_temp_path(file_info.dataset_name)
            temp_dir = Path(temp_dir_path) / file_id
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # 验证分片MD5（如果提供）
            if chunk_md5 and settings.enable_md5_check:
                actual_md5 = hashlib.md5(chunk_data).hexdigest()
                if actual_md5 != chunk_md5:
                    raise ValueError(f"分片 {chunk_index} MD5校验失败")
            
            # 保存分片文件
            chunk_file_path = temp_dir / f"chunk_{chunk_index}"
            async with aiofiles.open(chunk_file_path, "wb") as f:
                await f.write(chunk_data)
            
            # 更新文件信息
            file_info.uploaded_chunks.append(chunk_index)
            file_info.uploaded_chunks.sort()
            file_info.status = UploadStatus.UPLOADING
            file_info.updated_at = datetime.now().isoformat()
            
            return True
    
    async def merge_chunks(self, file_id: str, target_filename: str,
                          file_md5: Optional[str] = None) -> Tuple[bool, str]:
        """合并分片文件"""
        
        if file_id not in self._file_registry:
            raise ValueError(f"文件 {file_id} 信息不存在")
        
        file_info = self._file_registry[file_id]
        
        # 检查是否所有分片都已上传
        if not file_info.is_completed:
            missing_chunks = set(range(file_info.total_chunks)) - set(file_info.uploaded_chunks)
            raise ValueError(f"文件未完全上传，缺少分片: {sorted(missing_chunks)}")
        
        # 创建最终文件路径
        upload_dir_path = get_dataset_upload_path(file_info.dataset_name)
        final_file_path = Path(upload_dir_path) / target_filename
        final_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 合并分片
        temp_dir_path = get_dataset_temp_path(file_info.dataset_name)
        temp_dir = Path(temp_dir_path) / file_id
        async with aiofiles.open(final_file_path, "wb") as final_file:
            for chunk_index in range(file_info.total_chunks):
                chunk_file_path = temp_dir / f"chunk_{chunk_index}"
                if not chunk_file_path.exists():
                    raise ValueError(f"分片文件 {chunk_index} 不存在")
                
                async with aiofiles.open(chunk_file_path, "rb") as chunk_file:
                    chunk_data = await chunk_file.read()
                    await final_file.write(chunk_data)
        
        # 验证最终文件MD5（如果提供）
        if file_md5 and settings.enable_md5_check:
            actual_md5 = await self._calculate_file_md5(final_file_path)
            if actual_md5 != file_md5:
                # 删除错误的文件
                final_file_path.unlink(missing_ok=True)
                raise ValueError("文件MD5校验失败")
        
        # 清理临时文件
        await self._cleanup_temp_files(file_id)
        
        # 更新文件信息
        file_info.status = UploadStatus.COMPLETED
        file_info.file_path = str(final_file_path)
        file_info.updated_at = datetime.now().isoformat()
        
        return True, str(final_file_path)
    
    async def _calculate_file_md5(self, file_path: Path) -> str:
        """计算文件MD5值"""
        md5_hash = hashlib.md5()
        async with aiofiles.open(file_path, "rb") as f:
            async for chunk in self._read_chunks(f):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    async def _read_chunks(self, file_obj, chunk_size: int = 8192):
        """异步读取文件分块"""
        while True:
            chunk = await file_obj.read(chunk_size)
            if not chunk:
                break
            yield chunk
    
    async def _cleanup_temp_files(self, file_id: str):
        """清理临时文件"""
        temp_dir = Path(settings.temp_dir) / file_id
        if temp_dir.exists():
            for file in temp_dir.iterdir():
                file.unlink(missing_ok=True)
            temp_dir.rmdir()
    
    async def cleanup_expired_files(self):
        """清理过期的临时文件"""
        expire_time = datetime.now() - timedelta(hours=settings.chunk_expire_hours)
        
        temp_base_dir = Path(settings.temp_dir)
        if not temp_base_dir.exists():
            return
        
        for file_dir in temp_base_dir.iterdir():
            if not file_dir.is_dir():
                continue
            
            # 检查目录修改时间
            dir_mtime = datetime.fromtimestamp(file_dir.stat().st_mtime)
            if dir_mtime < expire_time:
                # 清理过期目录
                for file in file_dir.iterdir():
                    file.unlink(missing_ok=True)
                file_dir.rmdir()
                
                # 从注册表中移除
                file_id = file_dir.name
                if file_id in self._file_registry:
                    self._file_registry[file_id].status = UploadStatus.EXPIRED
    
    def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """获取文件信息"""
        return self._file_registry.get(file_id)
    
    def remove_file_info(self, file_id: str) -> bool:
        """移除文件信息"""
        if file_id in self._file_registry:
            del self._file_registry[file_id]
            return True
        return False


# 全局服务实例
file_upload_service = FileUploadService()
