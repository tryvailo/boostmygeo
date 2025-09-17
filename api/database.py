"""
Управление SQLite базой данных для хранения информации о пользователях и обработанных файлах
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional, Tuple
from config import REGISTRY_PATH

class Database:
    """Класс для работы с SQLite базой данных"""
    
    def __init__(self):
        self.db_path = REGISTRY_PATH
        self.init_db()
    
    def connect(self) -> sqlite3.Connection:
        """Создание подключения к базе данных"""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Инициализация базы данных и создание таблиц"""
        conn = self.connect()
        cur = conn.cursor()
        
        # Таблица для отслеживания IP адресов и обработанных файлов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS uploads (
                ip TEXT PRIMARY KEY,
                file_hash TEXT,
                first_seen_utc TEXT,
                last_seen_utc TEXT
            )
        """)  # IP может обрабатывать только один файл
        
        # Таблица для хранения email адресов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                ip TEXT,
                first_seen_utc TEXT,
                last_sent_utc TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def check_ip_file_access(self, ip: str, file_hash: str, allow_retry: bool = False) -> None:
        """
        Проверка доступа IP к обработке файла
        
        Args:
            ip: IP адрес
            file_hash: Хеш файла
            allow_retry: Разрешить повторную обработку того же файла
            
        Raises:
            PermissionError: Если доступ запрещен
        """
        conn = self.connect()
        cur = conn.cursor()
        
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        
        # Проверяем существующие записи для данного IP
        cur.execute("SELECT file_hash FROM uploads WHERE ip = ?", (ip,))
        row = cur.fetchone()
        
        if not row:
            # Первый раз для этого IP - разрешаем и сохраняем
            cur.execute(
                "INSERT INTO uploads VALUES (?, ?, ?, ?)",
                (ip, file_hash, now, now)
            )
        else:
            existing_hash = row[0]
            if existing_hash == file_hash:
                if not allow_retry:
                    conn.close()
                    raise PermissionError("Этот файл уже был обработан с данного IP адреса")
                else:
                    # Обновляем время последнего обращения
                    cur.execute(
                        "UPDATE uploads SET last_seen_utc = ? WHERE ip = ?",
                        (now, ip)
                    )
            else:
                # Разный файл - обновляем запись
                cur.execute(
                    "UPDATE uploads SET file_hash = ?, last_seen_utc = ? WHERE ip = ?",
                    (file_hash, now, ip)
                )
        
        conn.commit()
        conn.close()
    
    def save_email(self, email: str, ip: str) -> None:
        """
        Сохранение email адреса в базу
        
        Args:
            email: Email адрес
            ip: IP адрес пользователя
        """
        conn = self.connect()
        cur = conn.cursor()
        
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        
        # Пытаемся вставить новый email
        try:
            cur.execute(
                "INSERT INTO emails (email, ip, first_seen_utc, last_sent_utc) VALUES (?, ?, ?, ?)",
                (email, ip, now, now)
            )
        except sqlite3.IntegrityError:
            # Email уже существует - обновляем время последней отправки
            cur.execute(
                "UPDATE emails SET last_sent_utc = ?, ip = ? WHERE email = ?",
                (now, ip, email)
            )
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Tuple[int, int]:
        """
        Получение статистики
        
        Returns:
            Tuple[количество уникальных IP, количество уникальных email]
        """
        conn = self.connect()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM uploads")
        ip_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM emails")
        email_count = cur.fetchone()[0]
        
        conn.close()
        return ip_count, email_count

# Глобальный экземпляр базы данных
db = Database()