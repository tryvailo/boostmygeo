"""
Обработка файлов CSV/TSV/XLSX с поддержкой колонок Country, Prompt, Website
"""

import os
import pandas as pd
from typing import Tuple
from urllib.parse import urlparse
from config import MAX_ROWS_PROCESS

class FileProcessor:
    """Класс для обработки загруженных файлов"""
    
    @staticmethod
    def extract_domain_from_url(url: str) -> str:
        """
        Извлечение домена из URL
        
        Args:
            url: URL для обработки
            
        Returns:
            Домен без www префикса
        """
        if not url or not isinstance(url, str):
            return ""
        
        # Если это уже домен без протокола
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        try:
            netloc = urlparse(url).netloc.lower()
            return netloc[4:] if netloc.startswith("www.") else netloc
        except:
            return ""
    
    @staticmethod
    def process_file(file_path: str) -> Tuple[pd.DataFrame, int]:
        """
        Обработка файла и извлечение данных
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Tuple[DataFrame с данными, количество обработанных строк]
            
        Raises:
            ValueError: Если файл неподдерживаемого формата или отсутствуют обязательные колонки
        """
        ext = os.path.splitext(file_path.lower())[1]
        
        # Чтение файла в зависимости от расширения
        if ext == ".csv":
            df = pd.read_csv(file_path)
        elif ext == ".tsv":
            df = pd.read_csv(file_path, sep="\t")
        elif ext == ".xlsx":
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {ext}")
        
        # Нормализация названий колонок (приведение к нижнему регистру для поиска)
        df.columns = df.columns.str.strip()
        column_mapping = {}
        for col in df.columns:
            lower_col = col.lower()
            if lower_col in ['country', 'страна']:
                column_mapping[col] = 'Country'
            elif lower_col in ['prompt', 'query', 'запрос', 'запит']:
                column_mapping[col] = 'Prompt'
            elif lower_col in ['website', 'domain', 'домен', 'сайт']:
                column_mapping[col] = 'Website'
        
        # Переименование колонок
        df = df.rename(columns=column_mapping)
        
        # Проверка наличия обязательных колонок
        required_columns = ['Country', 'Prompt', 'Website']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"В файле отсутствуют обязательные колонки: {', '.join(missing_columns)}")
        
        # Очистка и нормализация данных
        df['Country'] = df['Country'].astype(str).str.strip()
        df['Prompt'] = df['Prompt'].astype(str).str.strip()
        df['Website'] = df['Website'].astype(str).str.strip()
        
        # Удаление строк с пустыми значениями в обязательных колонках
        df = df[
            (df['Country'] != '') & 
            (df['Prompt'] != '') & 
            (df['Website'] != '')
        ].reset_index(drop=True)
        
        # Нормализация доменов (извлечение домена из URL если указан полный URL)
        df['target_domain'] = df['Website'].apply(FileProcessor.extract_domain_from_url)
        
        # Удаление строк где не удалось извлечь домен
        df = df[df['target_domain'] != ''].reset_index(drop=True)
        
        # Ограничение на количество строк (жесткий лимит MVP)
        original_count = len(df)
        df = df.head(MAX_ROWS_PROCESS)
        processed_count = len(df)
        
        return df, processed_count
    
    @staticmethod
    def validate_file_size(content: bytes, max_size_mb: int) -> None:
        """
        Проверка размера файла
        
        Args:
            content: Содержимое файла в байтах
            max_size_mb: Максимальный размер в МБ
            
        Raises:
            ValueError: Если файл слишком большой
        """
        size_mb = len(content) / (1024 * 1024)
        if size_mb > max_size_mb:
            raise ValueError(f"Файл слишком большой: {size_mb:.2f}МБ > {max_size_mb}МБ")
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Получение расширения файла"""
        if not filename:
            return ".csv"  # Дефолтное расширение
        return os.path.splitext(filename.lower())[1] or ".csv"