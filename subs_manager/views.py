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
from django.http import JsonResponse
from django.utils import timezone
from django.utils.translation import gettext as _
import numpy as np
from datetime import datetime, timedelta

# Настроим логгер для отслеживания ошибок и важных событий
logger = logging.getLogger(__name__)

# Константы для настройки приложения
API_TIMEOUT = 15  # увеличиваем таймаут до 15 секунд
API_MAX_RETRIES = 3  # максимальное количество попыток
API_BASE_URL = "http://194.35.119.49:8090"
CACHE_TIMEOUT = 60 * 15  # 15 минут

def cache_api_response(timeout: int = CACHE_TIMEOUT):
    """
    Декоратор для кэширования ответов API.
    
    Используется для оптимизации производительности путем сохранения
    результатов API-запросов в кэше на определенное время.
    
    Args:
        timeout (int): Время жизни кэша в секундах. По умолчанию 15 минут.
    
    Returns:
        Callable: Декорированная функция, которая сначала проверяет кэш,
                и только при отсутствии данных делает запрос к API.
    
    Example:
        @cache_api_response(timeout=300)
        def get_user_data(user_id):
            return requests.get(f"/api/users/{user_id}")
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Создаем уникальный ключ кэша на основе аргументов функции
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

def fetch_api_data(url: str) -> Dict[str, Any]:
    """
    Безопасное получение данных от API с обработкой ошибок и кэшированием.
    
    Выполняет HTTP GET запрос к указанному URL с настроенным таймаутом
    и обработкой возможных ошибок.
    
    Args:
        url (str): URL для запроса
        
    Returns:
        Dict[str, Any]: Словарь с данными от API
        
    Raises:
        RequestException: при ошибках сети
        Timeout: при превышении времени ожидания
        ValueError: при некорректном ответе
    
    Example:
        try:
            data = fetch_api_data("https://api.example.com/data")
            process_data(data)
        except RequestException as e:
            handle_error(e)
    """
    for attempt in range(API_MAX_RETRIES):
        try:
            response = requests.get(url, timeout=API_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Timeout:
            if attempt == API_MAX_RETRIES - 1:
                logger.error(f"Timeout при запросе к {url} после {API_MAX_RETRIES} попыток")
                raise
            logger.warning(f"Timeout при запросе к {url}, попытка {attempt + 1} из {API_MAX_RETRIES}")
            time.sleep(1)  # Ждем секунду перед повторной попыткой
        except RequestException as e:
            if attempt == API_MAX_RETRIES - 1:
                logger.error(f"Ошибка при запросе к {url}: {str(e)}")
                raise
            logger.warning(f"Ошибка при запросе к {url}, попытка {attempt + 1} из {API_MAX_RETRIES}")
            time.sleep(1)

def validate_platform(platform: str) -> None:
    """
    Проверяет корректность названия платформы.
    
    Args:
        platform (str): Название платформы для проверки
        
    Raises:
        ValidationError: если платформа не входит в список поддерживаемых
    """
    valid_platforms = ["linkedin", "youtube", "medium", "instagram"]
    if platform.lower() not in valid_platforms:
        raise ValidationError(_(f"Недопустимая платформа: {platform}"))

def validate_profile_id(platform: str, profile_id: str) -> None:
    """
    Проверяет корректность ID профиля для каждой платформы.
    
    Args:
        platform (str): Название платформы
        profile_id (str): ID профиля для проверки
        
    Raises:
        ValidationError: если ID профиля некорректен
    """
    if not profile_id or not isinstance(profile_id, str):
        raise ValidationError(_(f"Некорректный ID профиля для {platform}"))

def calculate_trend_prediction(daily_stats: list, days_ahead: int = 2) -> list:
    """
    Рассчитывает прогноз на основе комбинации методов:
    1. Полиномиальная регрессия 2-й степени для определения тренда
    2. Экспоненциальное сглаживание для учета последних изменений
    
    Args:
        daily_stats: список словарей с данными за последние дни
        days_ahead: на сколько дней вперед делать прогноз
        
    Returns:
        list: список предсказанных значений с датами
    """
    if len(daily_stats) < 5:  # Нужно минимум 5 точек для надежного прогноза
        return []
        
    # Берем только последние 30 дней для прогноза
    recent_stats = daily_stats[-30:] if len(daily_stats) > 30 else daily_stats
    
    # Подготовка данных
    dates = [datetime.strptime(stat['date'], '%Y-%m-%d') for stat in recent_stats]
    days_nums = [(date - dates[0]).days for date in dates]
    counts = [stat.get('followers_count', stat.get('subscribers_count', 0)) for stat in recent_stats]
    
    # Полиномиальная регрессия 2-й степени
    poly_coeffs = np.polyfit(days_nums, counts, 2)
    poly = np.poly1d(poly_coeffs)
    
    # Экспоненциальное сглаживание для определения краткосрочного тренда
    alpha = 0.3  # Коэффициент сглаживания
    exp_smooth = counts[-1]  # Последнее известное значение
    last_changes = []
    
    # Рассчитываем последние изменения с экспоненциальным сглаживанием
    for i in range(len(counts)-1):
        change = counts[i+1] - counts[i]
        if not last_changes:
            last_changes.append(change)
        else:
            smoothed_change = alpha * change + (1 - alpha) * last_changes[-1]
            last_changes.append(smoothed_change)
    
    # Среднее изменение за последние дни с учетом сглаживания
    recent_trend = np.mean(last_changes[-5:]) if len(last_changes) >= 5 else last_changes[-1]
    
    # Расчет прогноза как комбинации полиномиальной регрессии и последнего тренда
    predictions = []
    last_date = dates[-1]
    last_count = counts[-1]
    
    for i in range(1, days_ahead + 1):
        future_date = last_date + timedelta(days=i)
        future_days = (future_date - dates[0]).days
        
        # Комбинируем полиномиальный прогноз с трендом
        poly_pred = poly(future_days)
        trend_pred = last_count + (recent_trend * i)
        
        # Взвешенная комбинация (70% полиномиальный прогноз, 30% линейный тренд)
        predicted_count = int(0.7 * poly_pred + 0.3 * trend_pred)
        
        predictions.append({
            'date': future_date.strftime('%Y-%m-%d'),
            'predicted_count': predicted_count
        })
    
    return predictions

@cache_page(CACHE_TIMEOUT)
def get_daily_statistics(request, platform: str) -> Any:
    """
    Получение ежедневной статистики для указанной платформы.
    
    Извлекает и обрабатывает статистические данные за день для заданной
    социальной платформы. Поддерживает кэширование результатов.
    
    Args:
        request: HTTP запрос
        platform (str): Название платформы
        
    Returns:
        HttpResponse: Отрендеренный шаблон с данными статистики
        
    Raises:
        ValidationError: при некорректной платформе
        RequestException: при ошибках API
    """
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

        # Рассчитываем прогноз
        predictions = calculate_trend_prediction(daily_stats)

        return render(request, 'subs_manager/daily_statistics.html', {
            'platform': platform.capitalize(),
            'daily_stats': daily_stats,
            'predictions': predictions,
        })

    except (ValidationError, RequestException, Timeout, ValueError) as e:
        logger.error(f"Ошибка при получении статистики для {platform}: {str(e)}")
        return render(request, 'subs_manager/error.html', {
            'message': _('Ошибка при получении данных: {}').format(str(e))
        })

@cache_page(CACHE_TIMEOUT)
def get_real_time_statistics(request) -> Any:
    """
    Получение статистики в реальном времени для всех платформ.
    
    Собирает текущие данные о подписчиках со всех поддерживаемых платформ
    и отображает их на главной странице.
    
    Args:
        request: HTTP запрос
        
    Returns:
        HttpResponse: Отрендеренный шаблон с текущей статистикой
        
    Example:
        При запросе главной страницы отображаются текущие показатели
        подписчиков для LinkedIn, YouTube, Medium и Instagram.
    """
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
            stats[f'{platform}_count'] = latest_data.get('count', _('Не удалось получить данные'))
            stats[f'{platform}_timestamp'] = latest_data.get('timestamp', _('Не удалось получить данные'))

        return render(request, 'subs_manager/real_time_statistics.html', stats)

    except (RequestException, Timeout, ValueError) as e:
        logger.error(f"Ошибка при получении статистики в реальном времени: {str(e)}")
        return render(request, 'subs_manager/error.html', {
            'message': f'Ошибка при получении данных: {str(e)}'
        })

@cache_page(CACHE_TIMEOUT)
def get_analytics(request) -> Any:
    """
    Получение аналитики по всем платформам.
    
    Собирает и анализирует данные о подписчиках со всех платформ,
    подготавливает статистические показатели для страницы аналитики.
    
    Args:
        request: HTTP запрос
        
    Returns:
        HttpResponse: Отрендеренный шаблон с аналитическими данными
    """
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

def update_statistics(request):
    """
    Обработчик для обновления статистики через AJAX-запрос.
    
    Получает актуальные данные со всех платформ и возвращает их в формате JSON.
    Используется для асинхронного обновления данных на странице.
    
    Args:
        request: HTTP запрос
        
    Returns:
        JsonResponse: Актуальные данные по всем платформам
        
    Example:
        Ответ содержит структуру вида:
        {
            'success': True,
            'linkedin': {'count': 1234, 'timestamp': '2024-04-24T08:59:00Z'},
            'youtube': {'count': 5678, 'timestamp': '2024-04-24T08:59:00Z'},
            ...
        }
    """
    try:
        # Получаем данные для всех платформ
        platforms_data = {
            'linkedin': fetch_api_data(f"{API_BASE_URL}/linkedin/latest?profile_id=gamsakhurdiya"),
            'youtube': fetch_api_data(f"{API_BASE_URL}/youtube/latest?channel_id=UCRhID0powzDpE4D2KuVKGHg"),
            'medium': fetch_api_data(f"{API_BASE_URL}/medium/latest?username=Eleron"),
            'instagram': fetch_api_data(f"{API_BASE_URL}/instagram/latest?username=nikog_bim")
        }

        # Формируем ответ
        response_data = {
            'success': True
        }

        # Добавляем данные по каждой платформе
        for platform, data in platforms_data.items():
            latest_data = data.get('latest_data', {})
            response_data[platform] = {
                'count': latest_data.get('count', 0),
                'timestamp': latest_data.get('timestamp', timezone.now().isoformat())
            }

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Ошибка при обновлении статистики: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
