"""
Конфигурация приложения AI Visibility MVP
"""

import os
import re
from typing import List

# OpenAI настройки
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
OPENAI_TIMEOUT = 90.0

# Домены для анализа (теперь используются как fallback)
OUR_DOMAINS: List[str] = [
    d.strip().lower()
    for d in os.environ.get("OUR_DOMAINS", "autodoc.eu").split(",")
    if d.strip()
]

# Файловые ограничения
ALLOW_RETRY_SAME_FILE = os.environ.get("ALLOW_RETRY_SAME_FILE", "false").lower() in ("1", "true", "yes")
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "10"))
MAX_ROWS_PROCESS = 10  # Жестко ограничено в MVP

# База данных
REGISTRY_PATH = os.environ.get("REGISTRY_PATH", ".ai_visibility_gate.sqlite")

# SMTP настройки
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
SMTP_FROM = os.environ.get("SMTP_FROM", "noreply@example.com")
SMTP_TLS = os.environ.get("SMTP_TLS", "true").lower() in ("1", "true", "yes")

# Email валидация
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Валидация конфигурации
def validate_config():
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY не установлен")
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
        raise ValueError("SMTP настройки не полные")