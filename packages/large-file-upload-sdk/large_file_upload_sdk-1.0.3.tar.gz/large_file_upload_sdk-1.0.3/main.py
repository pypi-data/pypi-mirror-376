"""
FastAPI 大文件上传服务器主应用
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from routers import router as upload_router, download_router
from services import file_upload_service

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("启动文件上传服务器...")
    
    # 启动时执行清理过期文件的任务
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # 关闭时清理
    cleanup_task.cancel()
    logger.info("文件上传服务器已关闭")


async def periodic_cleanup():
    """定期清理过期文件"""
    while True:
        try:
            await file_upload_service.cleanup_expired_files()
            logger.info("清理过期文件完成")
        except Exception as e:
            logger.error(f"清理过期文件失败: {e}")
        
        # 每小时执行一次清理
        await asyncio.sleep(3600)


# 创建FastAPI应用
app = FastAPI(
    title="文件上传服务器",
    description="星河启智二期用于上传大文件的server - 支持分片上传和断点续传",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"未处理的异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误"}
    )


# 健康检查接口
@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "1.0.0"
    }


# 服务信息接口
@app.get("/", tags=["服务信息"])
async def root():
    """服务信息"""
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "description": "星河启智二期用于上传大文件的server",
        "features": [
            "分片上传",
            "断点续传", 
            "MD5校验",
            "并发上传",
            "自动清理过期文件"
        ],
        "endpoints": {
            "upload_check": "/api/upload/check",
            "upload_chunk": "/api/upload/chunk", 
            "merge_chunks": "/api/upload/merge",
            "upload_status": "/api/upload/status/{file_id}",
            "cancel_upload": "/api/upload/{file_id}",
            "download": "/api/download/{filename}",
            "health": "/health",
            "docs": "/docs"
        },
        "config": {
            "max_file_size_gb": settings.max_file_size / (1024**3),
            "chunk_size_mb": settings.chunk_size / (1024**2),
            "chunk_expire_hours": settings.chunk_expire_hours,
            "enable_md5_check": settings.enable_md5_check
        }
    }


# 注册路由
app.include_router(upload_router)
app.include_router(download_router)


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"启动服务器: {settings.host}:{settings.port}")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
