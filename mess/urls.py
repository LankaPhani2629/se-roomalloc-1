from django.urls import path
from . import views

urlpatterns = [
    path('menu/', views.mess_menu_view, name='mess_menu'),
    path('menu/publish/', views.mess_menu_publish_view, name='mess_menu_publish'),
    path('attendance/skip/', views.mess_skip_meal_view, name='mess_skip_meal'),
    path('feedback/', views.mess_feedback_view, name='mess_feedback'),
    path('billing/', views.mess_billing_view, name='mess_billing'),
    path('reports/', views.mess_reports_view, name='mess_reports'),
]
