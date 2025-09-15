"""
认证中间件
"""
from fastapi import Header, HTTPException, Depends
from typing import Optional
from auth_service import get_auth_service, SimpleUserStore
from auth_models import AuthUser


async def get_current_user(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    auth_service: SimpleUserStore = Depends(get_auth_service)
) -> AuthUser:
    """
    获取当前认证用户
    
    从请求头中提取API Key并验证
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401, 
            detail="缺少API Key，请在请求头中添加 X-API-Key"
        )
    
    auth_user = auth_service.verify_api_key(x_api_key)
    if not auth_user:
        raise HTTPException(
            status_code=401, 
            detail="无效的API Key"
        )
    
    # 检查每日使用限制
    if auth_user.daily_remaining <= 0:
        raise HTTPException(
            status_code=429, 
            detail="今日上传次数已达上限"
        )
    
    return auth_user


def check_dataset_permission(auth_user: AuthUser, dataset_name: str) -> bool:
    """检查用户是否有权访问指定数据集"""
    # 如果allowed_datasets为空，表示可以访问所有数据集
    if not auth_user.allowed_datasets:
        return True
    
    return dataset_name in auth_user.allowed_datasets


def check_file_size_permission(auth_user: AuthUser, file_size: int) -> bool:
    """检查文件大小是否在用户限制内"""
    return file_size <= auth_user.max_file_size
