from django.urls import path
from . import views

urlpatterns = [
    path('', views.maintenance_list_view, name='maintenance_list'),
    path('request/create/', views.maintenance_create_view, name='maintenance_create'),
    path('request/<int:pk>/', views.maintenance_detail_view, name='maintenance_detail'),
    path('request/<int:pk>/update-status/', views.maintenance_update_status_view, name='maintenance_update_status'),
    path('request/<int:pk>/rate/', views.maintenance_rate_view, name='maintenance_rate'),
    path('staff/', views.maintenance_staff_manage_view, name='maintenance_staff_manage'),
]
