from django.contrib import admin
from django.urls import path
from subs_manager import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('real-time-statistics/', views.get_real_time_statistics, name='get_real_time_statistics'),
    path('', views.get_real_time_statistics, name='home'),
    path('statistics/daily/<str:platform>/', views.get_daily_statistics, name='get_daily_statistics'),  # Новый путь для статистики
    path('analytics/', views.get_analytics, name='get_analytics'),  # Новый путь для аналитики
]
