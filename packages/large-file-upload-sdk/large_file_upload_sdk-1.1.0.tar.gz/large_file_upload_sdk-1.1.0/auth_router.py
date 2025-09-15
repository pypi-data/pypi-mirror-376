"""
认证相关的API路由
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from auth_service import get_auth_service, SimpleUserStore
from auth_models import ApiKeyGenerate, ApiKeyResponse


router = APIRouter(prefix="/api/auth", tags=["认证管理"])


class SimpleApiKeyRequest(BaseModel):
    """简单的API Key请求"""
    user_id: int
    key_name: str = "默认API Key"


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    user_id: int
    username: str
    email: str
    is_active: bool
    allowed_datasets: List[str]
    max_file_size: int
    daily_upload_limit: int


@router.post("/generate-key", response_model=ApiKeyResponse)
async def generate_api_key(
    request: SimpleApiKeyRequest,
    auth_service: SimpleUserStore = Depends(get_auth_service)
):
    """
    为用户生成API Key
    
    用户只需要提供自己的user_id即可获取API Key
    """
    try:
        # 检查用户是否存在，如果不存在则自动创建
        user = auth_service.get_user(request.user_id)
        if not user:
            # 自动创建用户（简化流程）
            user = auth_service.create_user(
                username=f"user_{request.user_id}",
                email=f"user_{request.user_id}@example.com"
            )
        
        # 生成API Key
        key_generate = ApiKeyGenerate(
            key_name=request.key_name,
            permissions=["upload"],
            allowed_datasets=[]  # 空表示可以访问所有数据集
        )
        
        api_key_response = auth_service.create_api_key(request.user_id, key_generate)
        
        return api_key_response
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"生成API Key失败: {str(e)}")


@router.get("/user/{user_id}/info", response_model=UserInfoResponse)
async def get_user_info(
    user_id: int,
    auth_service: SimpleUserStore = Depends(get_auth_service)
):
    """获取用户信息"""
    user = auth_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UserInfoResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        allowed_datasets=user.allowed_datasets,
        max_file_size=user.max_file_size,
        daily_upload_limit=user.daily_upload_limit
    )


@router.get("/user/{user_id}/keys")
async def get_user_api_keys(
    user_id: int,
    auth_service: SimpleUserStore = Depends(get_auth_service)
) -> List[Dict[str, Any]]:
    """获取用户的所有API Key"""
    user = auth_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return auth_service.get_user_api_keys(user_id)


@router.delete("/user/{user_id}/keys/{key_id}")
async def revoke_api_key(
    user_id: int,
    key_id: str,
    auth_service: SimpleUserStore = Depends(get_auth_service)
):
    """撤销API Key"""
    success = auth_service.revoke_api_key(key_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="API Key不存在或不属于该用户")
    
    return {"message": "API Key已撤销"}


@router.post("/validate-key")
async def validate_api_key(
    api_key: str,
    auth_service: SimpleUserStore = Depends(get_auth_service)
):
    """验证API Key（用于测试）"""
    auth_user = auth_service.verify_api_key(api_key)
    if not auth_user:
        raise HTTPException(status_code=401, detail="无效的API Key")
    
    return {
        "valid": True,
        "user_id": auth_user.user_id,
        "username": auth_user.username,
        "permissions": auth_user.permissions,
        "daily_remaining": auth_user.daily_remaining
    }
