from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.bootstrap.ApiRouter import api_router, ops_api_router
from app.core.config.ServerConfig import settings
from app.test_support.bootstrap.TestAccountSeeder import ensure_test_account_exists
from app.core.db.Database import init_db, close_db
from app.core.locks.WriteLock import WriteConflictError, build_write_conflict_payload
from app.core.security.SensitiveWordFilter import init_sensitive_word_filter
from app.ops.auth.Service import OpsAuthService
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    init_sensitive_word_filter()
    await init_db()
    await OpsAuthService.ensure_bootstrap_data()
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
app.include_router(ops_api_router, prefix="/ops")

OPS_WEB_DIST = Path(__file__).resolve().parents[1] / "ops_web" / "dist"
OPS_WEB_ASSETS = OPS_WEB_DIST / "assets"

if OPS_WEB_ASSETS.exists():
    app.mount("/ops/assets", StaticFiles(directory=str(OPS_WEB_ASSETS)), name="ops-assets")


@app.exception_handler(WriteConflictError)
async def handle_write_conflict(_: Request, exc: WriteConflictError):
    return JSONResponse(
        status_code=409,
        content=build_write_conflict_payload(),
    )

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to Idle Cultivation Server",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/ops")
async def ops_index():
    index_file = OPS_WEB_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(
        status_code=503,
        content={
            "message": "ops_web 未构建",
            "hint": "请先在 idle_cultivation_server/ops_web 执行 npm install && npm run build",
        },
    )


@app.get("/ops/{full_path:path}")
async def ops_spa(full_path: str):
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    index_file = OPS_WEB_DIST / "index.html"
    target_file = OPS_WEB_DIST / full_path
    if target_file.exists() and target_file.is_file():
        return FileResponse(target_file)
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(
        status_code=503,
        content={
            "message": "ops_web 未构建",
            "hint": "请先在 idle_cultivation_server/ops_web 执行 npm install && npm run build",
        },
    )
