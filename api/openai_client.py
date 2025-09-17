"""
Клиент для работы с OpenAI Responses API
"""

from typing import Dict, List, Any, Optional
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT

class OpenAIClient:
    """Клиент для OpenAI Responses API"""
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY не установлен")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        self.timeout = OPENAI_TIMEOUT
    
    def search_with_web(self, query: str) -> Dict[str, Any]:
        """
        Выполнение запроса к OpenAI с веб-поиском
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Dict с источниками, usage и query
        """
        try:
            response = self.client.responses.create(
                model=self.model,
                input=f"{query} briefly and include sources citations.",
                tools=[{"type": "websearch"}],
                timeout=self.timeout
            )
            
            # Извлечение источников из ответа
            sources = self.extract_sources(response)
            usage = getattr(response, "usage", None)
            
            return {
                "sources": sources,
                "usage": usage,
                "query": query
            }
            
        except Exception as e:
            print(f"Ошибка OpenAI API: {e}")
            return {
                "sources": [],
                "usage": None,
                "query": query,
                "error": str(e)
            }
    
    def extract_sources(self, response) -> List[Dict[str, Any]]:
        """
        Извлечение источников из ответа OpenAI
        
        Args:
            response: Ответ от OpenAI API
            
        Returns:
            Список источников с URL и заголовками
        """
        try:
            sources = []
            
            # Получаем output items из ответа
            output_items = getattr(response, "output", [])
            
            for item in output_items:
                item_dict = item.__dict__ if hasattr(item, "__dict__") else {}
                
                # Ищем источники в различных полях
                if "sources" in item_dict:
                    for source in item_dict["sources"]:
                        source_dict = source.__dict__ if hasattr(source, "__dict__") else source
                        if isinstance(source_dict, dict) and "url" in source_dict:
                            sources.append({
                                "url": source_dict.get("url", ""),
                                "title": source_dict.get("title", ""),
                                "description": source_dict.get("description", "")
                            })
                
                # Дополнительная логика извлечения источников
                if "url" in item_dict:
                    sources.append({
                        "url": item_dict.get("url", ""),
                        "title": item_dict.get("title", ""),
                        "description": item_dict.get("description", "")
                    })
            
            return sources
            
        except Exception as e:
            print(f"Ошибка извлечения источников: {e}")
            return []

# Глобальный экземпляр клиента
openai_client = OpenAIClient()