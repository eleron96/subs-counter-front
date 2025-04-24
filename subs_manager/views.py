import logging
import requests
from django.shortcuts import render
from django.core.exceptions import ValidationError
from requests.exceptions import RequestException, Timeout
from django.views.decorators.cache import cache_page
from django.core.cache import cache
import json
from typing import Dict, Any, Union
from functools import wraps
import time

# Настроим логгер
logger = logging.getLogger(__name__)

# Константы
API_TIMEOUT = 5  # секунды
API_BASE_URL = "http://194.35.119.49:8090"
CACHE_TIMEOUT = 60 * 15  # 15 минут

def cache_api_response(timeout: int = CACHE_TIMEOUT):
    """
    Декоратор для кэширования ответов API.
    
    Args:
        timeout: Время жизни кэша в секундах
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Создаем ключ кэша на основе аргументов функции
            cache_key = f"api_response_{func.__name__}_{str(args)}_{str(kwargs)}"
            
            # Пробуем получить данные из кэша
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Получены данные из кэша для {cache_key}")
                return cached_data
            
            # Если данных нет в кэше, получаем их от API
            try:
                data = func(*args, **kwargs)
                # Сохраняем в кэш
                cache.set(cache_key, data, timeout)
                logger.debug(f"Данные сохранены в кэш для {cache_key}")
                return data
            except Exception as e:
                logger.error(f"Ошибка при получении данных: {str(e)}")
                raise
        return wrapper
    return decorator

@cache_api_response()
def fetch_api_data(url: str) -> Dict[str, Any]:
    """
    Безопасное получение данных от API с обработкой ошибок и кэшированием.
    
    Args:
        url: URL для запроса
        
    Returns:
        Dict с данными от API
        
    Raises:
        RequestException: при ошибках сети
        Timeout: при превышении времени ожидания
        ValueError: при некорректном ответе
    """
    try:
        response = requests.get(url, timeout=API_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Timeout:
        logger.error(f"Timeout при запросе к {url}")
        raise
    except RequestException as e:
        logger.error(f"Ошибка при запросе к {url}: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Некорректный JSON в ответе от {url}: {str(e)}")
        raise

def validate_platform(platform: str) -> None:
    """Проверяет корректность названия платформы."""
    valid_platforms = ["linkedin", "youtube", "medium", "instagram"]
    if platform.lower() not in valid_platforms:
        raise ValidationError(f"Недопустимая платформа: {platform}")

def validate_profile_id(platform: str, profile_id: str) -> None:
    """Проверяет корректность ID профиля для каждой платформы."""
    if not profile_id or not isinstance(profile_id, str):
        raise ValidationError(f"Некорректный ID профиля для {platform}")

@cache_page(CACHE_TIMEOUT)
def get_daily_statistics(request, platform: str) -> Any:
    """Получение ежедневной статистики для указанной платформы."""
    try:
        validate_platform(platform)
        
        # URL API для получения ежедневной статистики
        platform_urls = {
            "linkedin": f"{API_BASE_URL}/linkedin/daily-stats?profile_id=gamsakhurdiya",
            "youtube": f"{API_BASE_URL}/youtube/daily-stats?channel_id=UCRhID0powzDpE4D2KuVKGHg",
            "medium": f"{API_BASE_URL}/medium/daily-stats?username=Eleron",
            "instagram": f"{API_BASE_URL}/instagram/daily-stats?username=nikog_bim"
        }

        url = platform_urls.get(platform)
        if not url:
            raise ValidationError(f"Неизвестная платформа: {platform}")

        data = fetch_api_data(url)
        daily_stats = data.get('daily_stats', [])
        
        if not daily_stats:
            logger.warning(f"Нет данных для платформы: {platform}")
            daily_stats = [{'date': 'No data', 'subscribers_count': 'N/A'}]

        # Обработка данных в зависимости от платформы
        if platform == "linkedin":
            daily_stats = [
                {
                    'date': stat.get('date', 'Unknown'),
                    'followers_count': int(str(stat.get('followers_count', '0')).replace(',', ''))
                    if isinstance(stat.get('followers_count'), str) else stat.get('followers_count', 0)
                }
                for stat in daily_stats
            ]
        elif platform == "youtube":
            daily_stats = [
                {
                    'date': stat.get('date', 'Unknown'),
                    'subscribers_count': int(stat.get('subscribers_count', 0))
                    if isinstance(stat.get('subscribers_count'), int)
                    else int(str(stat.get('subscribers_count', '0')).replace(',', ''))
                }
                for stat in daily_stats
            ]
        elif platform == "medium":
            daily_stats = [
                {
                    'date': stat.get('date', 'Unknown'),
                    'followers_count': int(stat.get('followers_count', 0))
                    if isinstance(stat.get('followers_count'), int)
                    else int(stat.get('followers_count', '0').replace(',', ''))
                }
                for stat in daily_stats
            ]
        elif platform == "instagram":
            daily_stats = [
                {
                    'date': stat.get('date', 'Unknown'),
                    'followers_count': int(stat.get('followers_count', 0))
                    if isinstance(stat.get('followers_count'), int)
                    else int(str(stat.get('followers_count', '0')).replace(',', ''))
                }
                for stat in daily_stats
            ]

        return render(request, 'subs_manager/daily_statistics.html', {
            'platform': platform.capitalize(),
            'daily_stats': daily_stats,
        })

    except (ValidationError, RequestException, Timeout, ValueError) as e:
        logger.error(f"Ошибка при получении статистики для {platform}: {str(e)}")
        return render(request, 'subs_manager/error.html', {
            'message': f'Ошибка при получении данных: {str(e)}'
        })

@cache_page(CACHE_TIMEOUT)
def get_real_time_statistics(request) -> Any:
    """Получение статистики в реальном времени для всех платформ."""
    try:
        # Получаем данные для всех платформ
        platforms_data = {
            'linkedin': fetch_api_data(f"{API_BASE_URL}/linkedin/latest?profile_id=gamsakhurdiya"),
            'youtube': fetch_api_data(f"{API_BASE_URL}/youtube/latest?channel_id=UCRhID0powzDpE4D2KuVKGHg"),
            'medium': fetch_api_data(f"{API_BASE_URL}/medium/latest?username=Eleron"),
            'instagram': fetch_api_data(f"{API_BASE_URL}/instagram/latest?username=nikog_bim")
        }

        # Извлекаем данные
        stats = {}
        for platform, data in platforms_data.items():
            latest_data = data.get('latest_data', {})
            stats[f'{platform}_count'] = latest_data.get('count', 'Не удалось получить данные')
            stats[f'{platform}_timestamp'] = latest_data.get('timestamp', 'Не удалось получить данные')

        return render(request, 'subs_manager/real_time_statistics.html', stats)

    except (RequestException, Timeout, ValueError) as e:
        logger.error(f"Ошибка при получении статистики в реальном времени: {str(e)}")
        return render(request, 'subs_manager/error.html', {
            'message': f'Ошибка при получении данных: {str(e)}'
        })

@cache_page(CACHE_TIMEOUT)
def get_analytics(request) -> Any:
    """Получение аналитики по всем платформам."""
    try:
        # Получаем данные для всех платформ
        platforms_data = {
            'linkedin': fetch_api_data(f"{API_BASE_URL}/linkedin/latest?profile_id=gamsakhurdiya"),
            'youtube': fetch_api_data(f"{API_BASE_URL}/youtube/latest?channel_id=UCRhID0powzDpE4D2KuVKGHg"),
            'medium': fetch_api_data(f"{API_BASE_URL}/medium/latest?username=Eleron"),
            'instagram': fetch_api_data(f"{API_BASE_URL}/instagram/latest?username=nikog_bim")
        }

        # Извлекаем и обрабатываем данные
        stats = {}
        for platform, data in platforms_data.items():
            count = data.get('latest_data', {}).get('count', 0)
            # Преобразуем строковые значения в числа
            stats[f'{platform}_count'] = int(str(count).replace(',', '')) if isinstance(count, str) else int(count)

        return render(request, 'subs_manager/analytics.html', stats)

    except (RequestException, Timeout, ValueError) as e:
        logger.error(f"Ошибка при получении аналитики: {str(e)}")
        return render(request, 'subs_manager/error.html', {
            'message': f'Ошибка при получении данных: {str(e)}'
        })
