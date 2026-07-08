"""
配置管理模块 - 从环境变量加载应用配置

从 .env 文件读取环境变量并转换为应用配置，支持多种配置方式的兼容。

配置项说明:
    DB_CONFIG: PostgreSQL 数据库连接配置
        - host: 数据库服务器地址，默认 localhost
        - port: 数据库端口，默认 5432
        - database: 数据库名称，默认 sensor_data
        - user: 数据库用户名，默认 postgres
        - password: 数据库密码（必须在 .env 中配置）

    LOG_FILE_PATH: 日志文件路径，默认 logs/webhook.log
        支持相对路径和绝对路径，日志文件会自动轮转（每 10MB 保留 5 个备份）

    SECRET_KEY: Flask 会话加密密钥（生产环境必须修改）
        - 用途：加密会话 cookie,防止 CSRF 攻击
        - 建议：使用随机字符串，长度至少 32 字符

    AI_CONFIG: AI 服务配置（用于农事助手功能）
        - api_keys: API 密钥列表（逗号分隔），支持多个密钥负载均衡
        - api_key: 第一个密钥（向后兼容）
        - model_name: 大模型名称，默认 glm-4.7-flash
        - api_base_url: AI API 地址，默认智谱 AI 地址
        - timeout: API 请求超时时间（秒），默认 120 秒

为什么需要这个功能:
    - 集中管理配置，避免硬编码在代码中
    - 支持不同环境（开发、测试、生产）的配置切换
    - 配置项有默认值，方便快速部署
    - 支持 AI 多密钥负载均衡，提高服务可用性
"""
import os
from dotenv import load_dotenv

# 从 .env 文件加载环境变量
load_dotenv()

# 数据库配置
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),      # 数据库主机
    "port": int(os.getenv("DB_PORT", "5432")),      # 数据库端口
    "database": os.getenv("DB_NAME", "sensor_data"),# 数据库名
    "user": os.getenv("DB_USER", "postgres"),       # 数据库用户
    "password": os.getenv("DB_PASSWORD", "")        # 数据库密码（空值表示未配置）
}

# 日志配置
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", os.path.join(os.path.dirname(__file__), "logs", "webhook.log"))

# 安全配置
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# ==============================================================================
# AI 服务配置
# ==============================================================================
# 支持多个 API 密钥（逗号分隔），实现负载均衡
# 示例：AI_API_KEY="key1,key2,key3"
_raw_keys = os.getenv("AI_API_KEY", "")
_api_keys = [k.strip() for k in _raw_keys.split(",") if k.strip()]

AI_CONFIG = {
    "api_keys": _api_keys,                         # API 密钥列表（用于轮询选择）
    "api_key": _api_keys[0] if _api_keys else "",  # 第一个密钥（向后兼容）
    "model_name": os.getenv("AI_MODEL_NAME", "glm-4.7-flash"),  # 大模型名称
    "api_base_url": os.getenv("AI_API_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),  # API 地址
    "timeout": int(os.getenv("AI_TIMEOUT", "120"))  # 超时时间（秒）
}
