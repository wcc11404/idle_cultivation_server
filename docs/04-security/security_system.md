# 服务安全系统文档

## 目录

1. [账号安全](#1-账号安全)
2. [身份认证与授权](#2-身份认证与授权)
3. [防作弊系统](#3-防作弊系统)
4. [数据安全](#4-数据安全)
5. [内容安全](#5-内容安全)
6. [待改进措施](#6-待改进措施)

---

## 1. 账号安全

### 1.1 用户名验证

**位置**: `app/core/security/Validator.py`

**规则**:
- 长度限制：4-20个字符
- 字符限制：只能包含英文、数字、下划线
- 正则表达式：`^[a-zA-Z0-9_]+$`
- 唯一性检查：用户名不能重复

**实现**:
```python
@staticmethod
def validate_username(username: str) -> Tuple[bool, str]:
    if not username or not isinstance(username, str):
        return False, "用户名不能为空"
    
    username = username.strip()
    
    if len(username) < 4 or len(username) > 20:
        return False, "用户名长度必须在4-20位之间"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含英文、数字和下划线"
    
    return True, "用户名合法"
```

### 1.2 密码验证

**位置**: `app/core/security/Validator.py`

**规则**:
- 长度限制：6-20个字符
- 字符限制：只能包含英文、数字、英文标点符号
- 正则表达式：`^[a-zA-Z0-9!"#$%&'()*+,-./:;<=>?@[\\\]^_`{|}~]+$`
- 用户名密码不能相同

**实现**:
```python
@staticmethod
def validate_password(password: str) -> Tuple[bool, str]:
    if not password or not isinstance(password, str):
        return False, "密码不能为空"
    
    if len(password) < 6 or len(password) > 20:
        return False, "密码长度必须在6-20位之间"
    
    if not re.match(r'^[a-zA-Z0-9!"#$%&\'()*+,-./:;<=>?@[\\\]^_`{|}~]+$', password):
        return False, "密码只能包含英文、数字和英文标点符号"
    
    return True, "密码合法"
```

### 1.3 密码加密存储

**位置**: `app/core/security/Security.py`

**算法**: bcrypt

**实现**:
```python
def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    if len(password) > 72:
        password = password[:72]
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
```

**特点**:
- 使用bcrypt算法自动加盐
- 密码长度限制为72字符（bcrypt限制）
- 哈希值长度固定，防止彩虹表攻击

---

## 2. 身份认证与授权

### 2.1 Token认证机制

**位置**: `app/core/security/Security.py`

**算法**: JWT (JSON Web Token)

**实现**:
```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    """解码令牌"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None
```

**特点**:
- 使用JWT标准，包含过期时间
- Token有效期可配置（默认7天）
- 使用密钥签名，防止篡改

### 2.2 Token版本控制

**位置**: `app/core/security/Security.py`

**机制**: 每次登录更新token_version，强制旧token失效

**实现**:
```python
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Account:
    """获取当前用户"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOKEN")
    
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    
    account = await Account.get_or_none(id=account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ACCOUNT_NOT_FOUND")
    
    if account.token_version != token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="KICKED_OUT")
    
    return account
```

**作用**:
- 防止多设备同时登录
- 支持强制下线功能
- 密码修改后自动踢出所有设备

### 2.3 API认证要求

**规则**:
- 除注册、登录、排行榜等公开接口外，所有API都需要认证
- 认证方式：请求头携带 `Authorization: Bearer <token>`
- 未认证请求返回401错误

---

## 3. 防作弊系统

### 3.1 修炼系统防加速

**位置**: `app/game/application/AntiCheatSystem.py`

**机制**: 验证上报次数与时间间隔是否匹配

**实现**:
```python
@staticmethod
def validate_cultivation_report(
    current_time: float,
    last_report_time: float,
    reported_count: int,
    tolerance: float = 0.1
) -> Tuple[bool, str]:
    """
    验证修炼上报是否合理
    
    规则：
    - 如果上报次数 < 实际时间差：合理
    - 如果上报次数 > 实际时间差 * (1 + tolerance)：不合理
    """
    if last_report_time == 0:
        return True, "首次上报"
    
    actual_interval = current_time - last_report_time
    max_acceptable = actual_interval * (1 + tolerance)
    
    if reported_count > max_acceptable:
        reason = f"上报次数异常：上报{reported_count}次，实际间隔{actual_interval:.1f}秒，最大允许{max_acceptable:.1f}次"
        return False, reason
    
    return True, "验证通过"
```

**容差**: 10%（允许一定的网络延迟和计算误差）

### 3.2 历练系统防加速

**位置**: `app/game/domain/lianli/LianliSystem.py`

**机制**: 验证战斗结算时间是否合理

**实现**:
```python
if index < 0:
    # 首个事件前主动退出：仅清理战斗态，不做时间校验
    return {"success": True, "reason_code": "LIANLI_FINISH_PARTIALLY_SETTLED"}
else:
    battle_time_at_index = battle_timeline[index]["time"]
    expected_time = battle_time_at_index / speed
    actual_time = current_time - self.battle_start_time
    if actual_time < expected_time * 0.9:
        return {"success": False, "reason_code": "LIANLI_FINISH_TIME_INVALID"}
```

**验证逻辑**:
- 记录战斗开始时间
- 对 `index >= 0` 的结算请求计算预期战斗时长（考虑倍速）
- `index = -1` 视为“首个事件前退出”，不进入时间校验
- `index >= 0` 时，实际时长不能少于预期时长的90%
- 防止客户端加速播放战斗

### 3.3 可疑操作记录

**位置**: `app/game/application/AntiCheatSystem.py`

**机制**: 记录所有可疑操作，达到阈值可封号

**实现**:
```python
@staticmethod
async def record_suspicious_operation(
    account_id: str,
    operation_type: str,
    detail: str,
    account_system: 'AccountSystem',
    db_player_data
) -> int:
    """记录可疑操作"""
    count = account_system.increment_suspicious_operations()
    
    logger.warning(
        f"[ANTI_CHEAT] 可疑操作 - account_id: {account_id} - "
        f"type: {operation_type} - detail: {detail} - "
        f"count: {count}"
    )
    
    db_player_data.data["account_info"]["suspicious_operations_count"] = count
    await db_player_data.save()
    
    return count
```

**记录内容**:
- 账号ID
- 操作类型
- 详细信息
- 可疑操作次数

### 3.4 操作ID和Timestamp验证

**位置**: 所有API请求

**机制**: 每个请求必须包含operation_id和timestamp

**字段**:
- `operation_id`: 客户端生成的UUID，用于请求追踪和防重放
- `timestamp`: 客户端触发操作的时间戳（秒），用于时间验证

**作用**:
- 防止请求重放攻击
- 追踪每个操作的来源
- 验证请求时间合法性

---

## 4. 数据安全

### 4.1 数据库安全

**措施**:
- 使用ORM框架（Tortoise-ORM）防止SQL注入
- 参数化查询，不直接拼接SQL语句
- 数据库连接使用环境变量配置

### 4.2 敏感数据保护

**措施**:
- 密码使用bcrypt加密存储
- Token使用JWT签名
- 敏感配置使用环境变量（.env文件）
- 日志中不记录密码明文

### 4.3 数据验证

**位置**: 所有API接口

**措施**:
- 使用Pydantic进行数据类型验证
- 所有输入数据都经过验证后才处理
- 防止非法数据注入

---

## 5. 内容安全

### 5.1 昵称验证

**位置**: `app/core/security/Validator.py`

**规则**:
- 长度限制：4-10个字符
- 不能包含空格
- 不能包含不可见字符（零宽字符、不间断空格等）
- 不能全是数字
- 不能包含敏感词

**实现**:
```python
@staticmethod
def validate_nickname(nickname: str) -> Tuple[bool, str]:
    if not nickname or not isinstance(nickname, str):
        return False, "昵称不能为空"
    
    nickname = nickname.strip()
    
    if len(nickname) < 4 or len(nickname) > 10:
        return False, "昵称长度必须在4-10位之间"
    
    if ' ' in nickname:
        return False, "昵称不能包含空格"
    
    for char in Validator.INVISIBLE_CHARS:
        if char in nickname:
            return False, "昵称包含非法字符"
    
    if nickname.isdigit():
        return False, "昵称不能全是数字"
    
    try:
        sensitive_filter = get_sensitive_word_filter()
        if sensitive_filter.check(nickname):
            return False, "昵称包含敏感词汇"
    except Exception:
        # 检测器异常时放行，避免影响业务可用性
        pass
    
    return True, "昵称合法"
```

### 5.2 敏感词过滤

**工具**: 统一敏感词系统（`pyahocorasick` + 本地中英文词库）

**位置**: `requirements.txt`

**安装**:
```bash
pip install pyahocorasick
```

**使用**:
```python
from app.core.security.SensitiveWordFilter import get_sensitive_word_filter

sensitive_filter = get_sensitive_word_filter()
if sensitive_filter.check(nickname):
    return False, "昵称包含敏感词汇"
```

**特点**:
- Aho-Corasick 多模式高性能匹配
- 仓库内置词库，支持版本化管理
- 中文词表：`app/core/resources/sensitive_words_zh.txt`
- 英文词表：`app/core/resources/sensitive_words_en.txt`

---

## 6. 待改进措施

### 6.1 服务器防攻击

#### 6.1.1 DDoS防护
- [ ] 实现请求频率限制（Rate Limiting）
- [ ] 添加IP黑名单机制
- [ ] 使用CDN和负载均衡
- [ ] 配置防火墙规则

**建议实现**:
```python
from fastapi import FastAPI, Request
from fastapi.middleware import Middleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/game/data")
@limiter.limit("10/minute")
async def get_game_data(request: Request):
    pass
```

#### 6.1.2 SQL注入防护
- [x] 使用ORM框架（已实现）
- [ ] 添加输入过滤中间件
- [ ] 定期安全审计

#### 6.1.3 XSS防护
- [ ] 添加Content-Security-Policy头
- [ ] 对用户输入进行HTML转义
- [ ] 使用HTTPS传输

### 6.2 敏感词库完善

#### 6.2.1 自定义敏感词库
- [ ] 创建敏感词配置文件
- [ ] 支持动态更新敏感词
- [ ] 添加游戏特定敏感词（如"代练"、"刷钻"等）

**建议实现**:
```python
class SensitiveWordFilter:
    def __init__(self):
        self.words = set()
        self.load_words()
    
    def load_words(self):
        # 加载基础敏感词
        base_words = {
            "admin", "管理员", "gm", "客服", "官方",
            "代练", "刷钻", "外挂", "私服"
        }
        self.words.update(base_words)
        
        # 从文件加载自定义敏感词（示例可读取 app/core/resources/sensitive_words_zh.txt 与 sensitive_words_en.txt）
        try:
            with open("app/core/resources/sensitive_words_zh.txt", 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word:
                        self.words.add(word.lower())
        except FileNotFoundError:
            pass
```

#### 6.2.2 敏感词管理
- [ ] 提供敏感词管理接口
- [ ] 支持敏感词分类（政治、色情、广告等）
- [ ] 记录敏感词触发日志

### 6.3 请求频率限制

**建议实现**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# 不同接口设置不同限制
@app.post("/api/auth/login")
@limiter.limit("5/minute")  # 登录接口限制更严格
async def login(request: Request):
    pass

@app.post("/api/game/save")
@limiter.limit("30/minute")  # 保存接口限制较宽松
async def save_game(request: Request):
    pass
```

### 6.4 异常登录检测

**建议实现**:
- [ ] 记录登录IP和设备信息
- [ ] 检测异常登录地点
- [ ] 新设备登录提醒
- [ ] 可疑登录二次验证

**示例**:
```python
async def detect_abnormal_login(account_id: str, ip: str, device_info: dict):
    # 获取历史登录记录
    history = await LoginHistory.filter(account_id=account_id).order_by('-created_at').limit(10)
    
    # 检测新IP
    known_ips = {h.ip for h in history}
    if ip not in known_ips:
        await send_new_device_alert(account_id, ip, device_info)
    
    # 检测异常地点（需要IP地理位置库）
    location = get_ip_location(ip)
    if is_abnormal_location(history, location):
        await require_second_verification(account_id)
```

### 6.5 日志审计

**建议实现**:
- [ ] 记录所有敏感操作日志
- [ ] 日志分级（INFO、WARNING、ERROR）
- [ ] 日志定期归档和清理
- [ ] 异常操作自动告警

**示例**:
```python
import logging
from logging.handlers import RotatingFileHandler

# 配置日志轮转
handler = RotatingFileHandler(
    'logs/security.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

logger = logging.getLogger('security')
logger.addHandler(handler)

# 记录敏感操作
async def log_sensitive_operation(account_id: str, operation: str, detail: str):
    logger.warning(f"[SECURITY] {account_id} - {operation} - {detail}")
```

### 6.6 数据备份

**建议实现**:
- [ ] 定期自动备份数据库
- [ ] 备份文件加密存储
- [ ] 异地备份
- [ ] 定期恢复测试

**示例脚本**:
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup"
DB_NAME="idle_cultivation"

# 备份数据库
pg_dump $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 加密备份
gpg --encrypt --recipient admin@example.com $BACKUP_DIR/db_$DATE.sql.gz

# 上传到云存储
aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz.gpg s3://backup-bucket/

# 清理30天前的备份
find $BACKUP_DIR -name "*.gpg" -mtime +30 -delete
```

### 6.7 HTTPS加密传输

**建议实现**:
- [ ] 配置SSL证书
- [ ] 强制HTTPS重定向
- [ ] 启用HSTS头

**示例配置**:
```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()
app.add_middleware(HTTPSRedirectMiddleware)
```

### 6.8 验证码机制

**建议实现**:
- [ ] 登录失败多次后要求验证码
- [ ] 敏感操作（修改密码、解绑设备）要求验证码
- [ ] 使用图形验证码或短信验证码

**示例**:
```python
from fastapi_captcha import CaptchaMiddleware

app.add_middleware(
    CaptchaMiddleware,
    secret_key="your-secret-key",
    expire_seconds=300
)

@app.post("/api/auth/login")
async def login(request: LoginRequest, captcha: str = Form(...)):
    if not verify_captcha(captcha):
        raise HTTPException(status_code=400, detail="验证码错误")
    # 继续登录逻辑
```

### 6.9 IP黑名单

**建议实现**:
```python
from fastapi import Request, HTTPException

BLACKLIST = set()  # 可以从数据库或Redis加载

@app.middleware("http")
async def ip_filter(request: Request, call_next):
    client_ip = request.client.host
    
    if client_ip in BLACKLIST:
        raise HTTPException(status_code=403, detail="IP已被封禁")
    
    response = await call_next(request)
    return response
```

### 6.10 安全配置检查清单

- [ ] 修改默认端口
- [ ] 关闭调试模式
- [ ] 配置CORS白名单
- [ ] 设置合理的Token过期时间
- [ ] 定期更新依赖库
- [ ] 配置防火墙规则
- [ ] 启用访问日志
- [ ] 配置错误页面
- [ ] 定期安全审计

---

## 7. 安全最佳实践

### 7.1 开发阶段
1. 所有用户输入都要验证
2. 使用参数化查询，避免SQL注入
3. 敏感数据加密存储
4. 不在日志中记录敏感信息
5. 代码审查关注安全问题

### 7.2 部署阶段
1. 使用HTTPS
2. 配置防火墙
3. 定期备份数据
4. 监控异常访问
5. 及时更新依赖

### 7.3 运维阶段
1. 定期检查日志
2. 监控系统异常
3. 及时处理安全事件
4. 定期安全审计
5. 用户安全教育

---

## 8. 安全事件响应流程

### 8.1 发现异常
1. 日志监控发现异常
2. 用户举报
3. 自动告警

### 8.2 初步处理
1. 记录事件详情
2. 评估影响范围
3. 临时封禁可疑账号

### 8.3 深入调查
1. 分析攻击手段
2. 追溯攻击来源
3. 评估数据泄露风险

### 8.4 修复漏洞
1. 修复安全漏洞
2. 加强防护措施
3. 更新安全策略

### 8.5 事后总结
1. 编写事件报告
2. 改进安全措施
3. 用户通知（如需要）

---

## 9. 相关文件

- `app/core/security/Security.py` - 身份认证与密码加密
- `app/core/security/Validator.py` - 数据验证
- `app/game/application/AntiCheatSystem.py` - 防作弊系统
- `app/game/api/AuthApi.py` - 账号相关API
- `requirements.txt` - 依赖配置

---

## 10. 更新日志

- 2026-04-05: 创建文档，记录现有安全措施
- 待更新: 实现更多安全措施后更新文档
