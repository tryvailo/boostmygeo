"""
Расчет метрик для AI Visibility отчета с поддержкой индивидуальных доменов
"""

from typing import List, Dict, Any, Tuple, Optional
from urllib.parse import urlparse
from collections import Counter

class MetricsCalculator:
    """Класс для расчета метрик AI Visibility"""
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """
        Извлечение домена из URL
        
        Args:
            url: URL для обработки
            
        Returns:
            Домен без www префикса
        """
        try:
            netloc = urlparse(url).netloc.lower()
            return netloc[4:] if netloc.startswith("www.") else netloc
        except:
            return ""
    
    @staticmethod
    def calculate_aiv_score(sources: List[Dict], target_domain: str) -> float:
        """
        Расчет AIV-Score по формуле для конкретного домена
        
        Args:
            sources: Список источников
            target_domain: Целевой домен для анализа
            
        Returns:
            AIV-Score от 0 до 100
        """
        target_domain = target_domain.lower()
        N = len(sources)
        K = min(5, max(1, N)) if N > 0 else 1
        
        # 40% Inclusion - есть ли вообще источники
        inclusion = 1.0 if N > 0 else 0.0
        
        # Поиск рангов целевого домена
        our_ranks = [
            i + 1 for i, source in enumerate(sources)
            if MetricsCalculator.extract_domain(source.get("url", "")) == target_domain
        ]
        
        # 40% Presence × Prominence - есть ли мы и насколько высоко
        presence = 1.0 if our_ranks else 0.0
        prominence = (1.0 - (min(our_ranks) - 1) / K) if our_ranks else 0.0
        
        # 20% Depth - сколько у нас упоминаний (макс 5)
        depth = min(len(our_ranks), 5) / 5.0
        
        # Итоговый скор
        score = 100 * (0.40 * inclusion + 0.40 * (presence * prominence) + 0.20 * depth)
        
        return round(score, 1)
    
    @staticmethod
    def get_aiv_level(score: float) -> str:
        """Определение уровня AIV-Score"""
        if score <= 30:
            return "Low"
        elif score <= 60:
            return "Medium"  
        elif score <= 80:
            return "High"
        else:
            return "Dominant"
    
    @staticmethod
    def get_recommendation_label(mentions_count: int) -> str:
        """Генерация рекомендации AI"""
        if mentions_count > 0:
            return f"Рекомендується ({mentions_count})"
        else:
            return "Не рекомендується"
    
    @staticmethod
    def calculate_competitor_strength(sources: List[Dict], target_domain: str, k: int = 3) -> Tuple[Optional[float], str]:
        """
        Расчет силы конкурентов относительно целевого домена
        
        Args:
            sources: Список источников
            target_domain: Целевой домен
            k: Количество конкурентов для анализа
            
        Returns:
            Tuple[индекс силы, текстовое описание]
        """
        target_domain = target_domain.lower()
        competitor_ranks = []
        
        for i, source in enumerate(sources, 1):
            domain = MetricsCalculator.extract_domain(source.get("url", ""))
            if domain and domain != target_domain:
                competitor_ranks.append(i)
                if len(competitor_ranks) >= k:
                    break
        
        if not competitor_ranks:
            return None, "No competitors"
        
        avg_rank = sum(competitor_ranks) / len(competitor_ranks)
        
        if avg_rank <= 2:
            strength_label = "Strong"
        elif avg_rank <= 3.5:
            strength_label = "Moderate"
        else:
            strength_label = "Weak"
        
        return round(avg_rank, 2), strength_label
    
    @staticmethod
    def analyze_coverage_type(sources: List[Dict]) -> str:
        """
        Анализ типов источников
        
        Args:
            sources: Список источников
            
        Returns:
            Строка с описанием типов источников
        """
        if not sources:
            return "N/A"
        
        types = []
        for source in sources:
            url = source.get("url", "").lower()
            if any(keyword in url for keyword in ["forum", "reddit", "quora"]):
                types.append("Forum")
            elif any(keyword in url for keyword in ["/docs", "/help"]):
                types.append("Docs")
            elif any(keyword in url for keyword in ["/product", "/buy", "/shop"]):
                types.append("Product")
            elif any(keyword in url for keyword in ["/blog", "/review"]):
                types.append("Blog")
            else:
                types.append("Other")
        
        # Подсчет статистики
        counter = Counter(types)
        total = sum(counter.values())
        top_types = counter.most_common(2)
        
        return ", ".join([
            f"{type_name} ({round(count / total * 100)}%)"
            for type_name, count in top_types
        ])
    
    @staticmethod
    def calculate_metrics_for_query(sources: List[Dict], target_domain: str, country: str = "") -> Dict[str, Any]:
        """
        Расчет всех метрик для одного запроса
        
        Args:
            sources: Список источников
            target_domain: Целевой домен для анализа
            country: Страна запроса (для дополнительного контекста)
            
        Returns:
            Словарь с метриками
        """
        target_domain = target_domain.lower()
        
        # Подсчет упоминаний целевого домена
        our_mentions = 0
        best_rank = None
        
        for i, source in enumerate(sources, 1):
            domain = MetricsCalculator.extract_domain(source.get("url", ""))
            if domain == target_domain:
                our_mentions += 1
                if best_rank is None:
                    best_rank = i
        
        # Расчет всех метрик
        aiv_score = MetricsCalculator.calculate_aiv_score(sources, target_domain)
        competitor_index, competitor_label = MetricsCalculator.calculate_competitor_strength(sources, target_domain)
        
        # Список конкурентов (исключая наш домен)
        competitors = []
        for source in sources[:5]:  # Берем первые 5
            domain = MetricsCalculator.extract_domain(source.get("url", ""))
            if domain and domain != target_domain and domain not in competitors:
                competitors.append(domain)
        
        return {
            "Страна": country,
            "Целевой домен": target_domain,
            "Рекомендація АІ": MetricsCalculator.get_recommendation_label(our_mentions),
            "Позиція": best_rank or "",
            "Best Rank Explanation": (
                "Not visible" if best_rank is None 
                else f"Target domain appears at #{best_rank}"
            ),
            "AIV-Score": aiv_score,
            "AIV-Score Level": MetricsCalculator.get_aiv_level(aiv_score),
            "Mentions Count": our_mentions,
            "Конкуренти": ", ".join(competitors[:3]),  # Показываем топ-3 конкурентов
            "Competitor Strength Index": competitor_index,
            "Competitor Strength Label": competitor_label,
            "Coverage Type": MetricsCalculator.analyze_coverage_type(sources),
            "Total Sources": len(sources)
        }