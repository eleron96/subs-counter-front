from django.contrib import admin
from django.urls import path, include
from subs_manager import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # Добавляем URL для переключения языков
    path('real-time-statistics/', views.get_real_time_statistics, name='get_real_time_statistics'),
    path('', views.get_real_time_statistics, name='home'),
    path('statistics/daily/<str:platform>/', views.get_daily_statistics, name='get_daily_statistics'),  # Новый путь для статистики
    path('analytics/', views.get_analytics, name='get_analytics'),  # Новый путь для аналитики
    path('update-statistics/', views.update_statistics, name='update_statistics'),  # Новый маршрут для обновления данных
]
