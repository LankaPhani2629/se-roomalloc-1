from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_list_view, name='notifications_list'),
    path('<int:pk>/read/', views.mark_as_read_view, name='mark_as_read'),
    path('mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
]
