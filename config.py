import os
from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "sensor_data"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "")
}

LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", os.path.join(os.path.dirname(__file__), "logs", "webhook.log"))

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

AI_CONFIG = {
    "api_key": os.getenv("AI_API_KEY", ""),
    "model_name": os.getenv("AI_MODEL_NAME", "glm-4.7-flash"),
    "api_base_url": os.getenv("AI_API_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
    "timeout": int(os.getenv("AI_TIMEOUT", "120"))
}
