from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.ServerConfig import settings
from app.core.TestAccountSeeder import ensure_test_account_exists
from app.db.Database import init_db, close_db
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_db()
    await ensure_test_account_exists()
    yield
    await close_db()


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
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

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to Idle Cultivation Server",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }
