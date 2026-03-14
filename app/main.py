from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.config import settings
from app.db.database import init_db, close_db

# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 启动事件
@app.on_event("startup")
async def startup_event():
    """启动时初始化数据库"""
    await init_db()

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """关闭时关闭数据库连接"""
    await close_db()

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to Idle Cultivation Server",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }