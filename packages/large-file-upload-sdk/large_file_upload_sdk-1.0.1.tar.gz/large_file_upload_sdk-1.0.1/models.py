"""
数据模型定义
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class UploadStatus(str, Enum):
    """上传状态枚举"""
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class FileCheckRequest(BaseModel):
    """文件检查请求模型"""
    file_id: str = Field(..., description="文件唯一标识符")
    file_name: str = Field(..., description="原始文件名")
    file_size: int = Field(..., gt=0, description="文件总大小(字节)")
    file_md5: Optional[str] = Field(None, description="文件MD5值")
    total_chunks: int = Field(..., gt=0, description="分片总数")
    dataset_name: str = Field(..., description="数据集名称")
    
    @validator('file_id')
    def validate_file_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('文件ID不能为空')
        return v.strip()


class ChunkUploadRequest(BaseModel):
    """分片上传请求模型"""
    file_id: str = Field(..., description="文件唯一标识符")
    file_name: str = Field(..., description="原始文件名")
    file_size: int = Field(..., gt=0, description="文件总大小(字节)")
    file_md5: Optional[str] = Field(None, description="文件MD5值")
    chunk_index: int = Field(..., ge=0, description="当前分片序号(从0开始)")
    total_chunks: int = Field(..., gt=0, description="分片总数")
    chunk_size: int = Field(..., gt=0, description="当前分片大小(字节)")
    chunk_md5: Optional[str] = Field(None, description="当前分片MD5值")
    dataset_name: str = Field(..., description="数据集名称")
    
    @validator('chunk_index')
    def validate_chunk_index(cls, v, values):
        if 'total_chunks' in values and v >= values['total_chunks']:
            raise ValueError('分片序号不能大于等于分片总数')
        return v


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    code: int = Field(..., description="响应状态码")
    message: str = Field(..., description="响应消息")
    file_id: Optional[str] = Field(None, description="文件唯一标识符")
    file_name: Optional[str] = Field(None, description="文件名")
    file_url: Optional[str] = Field(None, description="文件访问URL")
    uploaded_chunks: Optional[List[int]] = Field(None, description="已上传的分片列表")
    is_completed: Optional[bool] = Field(None, description="是否上传完成")
    file_size: Optional[int] = Field(None, description="文件大小")
    progress: Optional[float] = Field(None, description="上传进度(百分比)")
    
    @classmethod
    def success(cls, message: str = "操作成功", **kwargs):
        """创建成功响应"""
        return cls(code=200, message=message, **kwargs)
    
    @classmethod
    def error(cls, message: str = "操作失败", code: int = 500, **kwargs):
        """创建错误响应"""
        return cls(code=code, message=message, **kwargs)


class FileMergeRequest(BaseModel):
    """文件合并请求模型"""
    file_id: str = Field(..., description="文件唯一标识符")
    file_name: str = Field(..., description="原始文件名")
    total_chunks: int = Field(..., gt=0, description="分片总数")
    file_md5: Optional[str] = Field(None, description="文件MD5值用于校验")
    dataset_name: str = Field(..., description="数据集名称")


class FileInfo(BaseModel):
    """文件信息模型"""
    file_id: str
    file_name: str
    file_size: int
    file_md5: Optional[str] = None
    total_chunks: int
    uploaded_chunks: List[int] = []
    status: UploadStatus = UploadStatus.PENDING
    created_at: str
    updated_at: str
    file_path: Optional[str] = None
    dataset_name: str
    
    @property
    def progress(self) -> float:
        """计算上传进度"""
        if self.total_chunks == 0:
            return 0.0
        return (len(self.uploaded_chunks) / self.total_chunks) * 100
    
    @property
    def is_completed(self) -> bool:
        """判断是否上传完成"""
        return len(self.uploaded_chunks) == self.total_chunks
