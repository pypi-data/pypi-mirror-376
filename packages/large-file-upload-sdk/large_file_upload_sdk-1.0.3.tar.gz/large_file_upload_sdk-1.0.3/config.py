"""
配置文件
"""
import os
from typing import List, Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务器配置
    app_name: str = "file-upload-server"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # 文件上传配置
    upload_base_dir: str = "/cpfs-nfs/sais/data-plaza-svc/datasets"  # 数据集基础路径，可通过环境变量UPLOAD_BASE_DIR覆盖
    temp_dir: str = "/cpfs-nfs/sais/data-plaza-svc/temp"  # 临时路径，放在数据盘上
    max_file_size: int = 500 * 1024 * 1024 * 1024  # 500GB
    chunk_size: int = 10 * 1024 * 1024  # 10MB
    chunk_expire_hours: int = 24
    
    # 允许的文件类型 (空列表表示允许所有类型)
    allowed_file_types: List[str] = []
    
    # 是否启用MD5校验
    enable_md5_check: bool = True
    
    # 并发上传限制
    max_concurrent_uploads: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """获取配置实例"""
    return Settings()


def get_dataset_upload_path(dataset_name: str) -> str:
    """根据数据集名称生成上传路径"""
    if not dataset_name:
        raise ValueError("数据集名称不能为空")
    
    # 生成路径: /cpfs-nfs/sais/data-plaza-svc/datasets/{datasetName}/full/download/
    return os.path.join(settings.upload_base_dir, dataset_name, "full", "download")


def get_dataset_temp_path(dataset_name: str) -> str:
    """根据数据集名称生成临时路径"""
    # 临时路径统一使用配置的临时目录，避免在数据集目录中留下临时文件
    return settings.temp_dir


# 全局配置实例
settings = get_settings()

# 确保临时目录存在
os.makedirs(settings.temp_dir, exist_ok=True)
