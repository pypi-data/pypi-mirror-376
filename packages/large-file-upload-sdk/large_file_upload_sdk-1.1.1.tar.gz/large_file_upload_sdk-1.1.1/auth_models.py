"""
用户认证相关的数据模型
"""
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel
import hashlib
import secrets
import hmac


class User(BaseModel):
    """用户模型"""
    user_id: int
    username: str
    email: str
    is_active: bool = True
    created_at: datetime
    
    # 权限相关
    allowed_datasets: List[str] = []  # 允许访问的数据集列表，空表示全部
    max_file_size: int = 100 * 1024 * 1024  # 最大文件大小（字节）
    daily_upload_limit: int = 100  # 每日上传次数限制


class ApiKey(BaseModel):
    """API Key模型"""
    key_id: str
    user_id: int
    key_name: str  # 用户给API Key起的名字
    key_hash: str  # API Key的哈希值（安全存储）
    
    # 权限和限制
    permissions: List[str] = ["upload"]  # 权限列表
    allowed_datasets: List[str] = []  # 允许访问的数据集，空表示继承用户权限
    
    # 状态和时间
    is_active: bool = True
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None  # 可选的过期时间
    
    # 使用统计
    usage_count: int = 0
    daily_usage: int = 0
    last_reset_date: datetime


class AuthRequest(BaseModel):
    """认证请求模型"""
    api_key: str


class AuthUser(BaseModel):
    """认证后的用户信息"""
    user_id: int
    username: str
    permissions: List[str]
    allowed_datasets: List[str]
    max_file_size: int
    daily_remaining: int


class ApiKeyGenerate(BaseModel):
    """生成API Key的请求"""
    key_name: str
    expires_days: Optional[int] = None  # 可选的过期天数
    permissions: List[str] = ["upload"]
    allowed_datasets: List[str] = []


class ApiKeyResponse(BaseModel):
    """API Key生成响应"""
    key_id: str
    api_key: str  # 只在生成时返回一次
    key_name: str
    permissions: List[str]
    expires_at: Optional[datetime]
    created_at: datetime


# API Key管理类
class ApiKeyManager:
    """API Key管理器"""
    
    @staticmethod
    def generate_api_key(user_id: int) -> str:
        """生成API Key"""
        # 生成随机字符串
        random_part = secrets.token_urlsafe(16)[:16]
        
        # 生成校验码
        message = f"{user_id}:{random_part}"
        checksum = hashlib.sha256(message.encode()).hexdigest()[:8]
        
        # 组装API Key
        api_key = f"ak_{user_id}_{random_part}_{checksum}"
        return api_key
    
    @staticmethod
    def validate_api_key(api_key: str) -> Optional[dict]:
        """验证API Key格式并提取信息"""
        try:
            parts = api_key.split('_')
            if len(parts) != 4 or parts[0] != 'ak':
                return None
            
            prefix, user_id_str, random_part, checksum = parts
            user_id = int(user_id_str)
            
            # 验证校验码
            message = f"{user_id}:{random_part}"
            expected_checksum = hashlib.sha256(message.encode()).hexdigest()[:8]
            
            if not hmac.compare_digest(checksum, expected_checksum):
                return None
            
            return {
                "user_id": user_id,
                "random_part": random_part,
                "checksum": checksum
            }
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """生成API Key的安全哈希值用于存储"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key_hash(api_key: str, stored_hash: str) -> bool:
        """验证API Key与存储的哈希值是否匹配"""
        return hmac.compare_digest(
            ApiKeyManager.hash_api_key(api_key),
            stored_hash
        )
