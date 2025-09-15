"""
认证服务 - 处理API Key生成、验证和管理
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import os
from auth_models import (
    User, ApiKey, AuthUser, ApiKeyGenerate, ApiKeyResponse, 
    ApiKeyManager
)


class SimpleUserStore:
    """简单的用户存储（生产环境应该用数据库）"""
    
    def __init__(self, data_file: str = "users.json"):
        self.data_file = data_file
        self.users = self._load_users()
        self.api_keys = self._load_api_keys()
    
    def _load_users(self) -> Dict[int, User]:
        """加载用户数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        int(uid): User(**user_data) 
                        for uid, user_data in data.get('users', {}).items()
                    }
            except Exception:
                pass
        return {}
    
    def _load_api_keys(self) -> Dict[str, ApiKey]:
        """加载API Key数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        key_id: ApiKey(**key_data) 
                        for key_id, key_data in data.get('api_keys', {}).items()
                    }
            except Exception:
                pass
        return {}
    
    def _save_data(self):
        """保存数据到文件"""
        data = {
            'users': {
                str(uid): user.dict() 
                for uid, user in self.users.items()
            },
            'api_keys': {
                key_id: api_key.dict() 
                for key_id, api_key in self.api_keys.items()
            }
        }
        
        # 处理datetime序列化
        def datetime_handler(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=datetime_handler)
    
    def get_user(self, user_id: int) -> Optional[User]:
        """获取用户"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def create_user(self, username: str, email: str, **kwargs) -> User:
        """创建用户"""
        user_id = max(self.users.keys()) + 1 if self.users else 1
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            created_at=datetime.now(),
            **kwargs
        )
        self.users[user_id] = user
        self._save_data()
        return user
    
    def create_api_key(self, user_id: int, key_generate: ApiKeyGenerate) -> ApiKeyResponse:
        """为用户创建API Key"""
        user = self.get_user(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        # 生成API Key
        api_key = ApiKeyManager.generate_api_key(user_id)
        key_hash = ApiKeyManager.hash_api_key(api_key)
        
        # 创建API Key记录
        key_id = f"key_{user_id}_{len([k for k in self.api_keys.values() if k.user_id == user_id]) + 1}"
        
        expires_at = None
        if key_generate.expires_days:
            expires_at = datetime.now() + timedelta(days=key_generate.expires_days)
        
        api_key_obj = ApiKey(
            key_id=key_id,
            user_id=user_id,
            key_name=key_generate.key_name,
            key_hash=key_hash,
            permissions=key_generate.permissions,
            allowed_datasets=key_generate.allowed_datasets,
            created_at=datetime.now(),
            expires_at=expires_at,
            last_reset_date=datetime.now().date()
        )
        
        self.api_keys[key_id] = api_key_obj
        self._save_data()
        
        return ApiKeyResponse(
            key_id=key_id,
            api_key=api_key,  # 只在创建时返回
            key_name=key_generate.key_name,
            permissions=key_generate.permissions,
            expires_at=expires_at,
            created_at=api_key_obj.created_at
        )
    
    def verify_api_key(self, api_key: str) -> Optional[AuthUser]:
        """验证API Key并返回用户信息"""
        # 验证API Key格式
        key_info = ApiKeyManager.validate_api_key(api_key)
        if not key_info:
            return None
        
        user_id = key_info["user_id"]
        
        # 查找匹配的API Key
        for api_key_obj in self.api_keys.values():
            if (api_key_obj.user_id == user_id and 
                api_key_obj.is_active and
                ApiKeyManager.verify_api_key_hash(api_key, api_key_obj.key_hash)):
                
                # 检查是否过期
                if api_key_obj.expires_at and datetime.now() > api_key_obj.expires_at:
                    return None
                
                # 获取用户信息
                user = self.get_user(user_id)
                if not user or not user.is_active:
                    return None
                
                # 更新使用统计
                self._update_api_key_usage(api_key_obj)
                
                # 计算今日剩余次数
                daily_remaining = max(0, user.daily_upload_limit - api_key_obj.daily_usage)
                
                return AuthUser(
                    user_id=user.user_id,
                    username=user.username,
                    permissions=api_key_obj.permissions,
                    allowed_datasets=api_key_obj.allowed_datasets or user.allowed_datasets,
                    max_file_size=user.max_file_size,
                    daily_remaining=daily_remaining
                )
        
        return None
    
    def _update_api_key_usage(self, api_key_obj: ApiKey):
        """更新API Key使用统计"""
        now = datetime.now()
        
        # 如果是新的一天，重置每日使用计数
        if api_key_obj.last_reset_date < now.date():
            api_key_obj.daily_usage = 0
            api_key_obj.last_reset_date = now.date()
        
        # 更新使用统计
        api_key_obj.usage_count += 1
        api_key_obj.daily_usage += 1
        api_key_obj.last_used_at = now
        
        self._save_data()
    
    def get_user_api_keys(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的所有API Key（不包含实际key值）"""
        user_keys = []
        for api_key in self.api_keys.values():
            if api_key.user_id == user_id:
                user_keys.append({
                    "key_id": api_key.key_id,
                    "key_name": api_key.key_name,
                    "permissions": api_key.permissions,
                    "is_active": api_key.is_active,
                    "created_at": api_key.created_at,
                    "last_used_at": api_key.last_used_at,
                    "expires_at": api_key.expires_at,
                    "usage_count": api_key.usage_count,
                    "daily_usage": api_key.daily_usage
                })
        return user_keys
    
    def revoke_api_key(self, key_id: str, user_id: int) -> bool:
        """撤销API Key"""
        api_key = self.api_keys.get(key_id)
        if api_key and api_key.user_id == user_id:
            api_key.is_active = False
            self._save_data()
            return True
        return False


# 全局认证服务实例
auth_service = SimpleUserStore()


def get_auth_service() -> SimpleUserStore:
    """获取认证服务实例"""
    return auth_service