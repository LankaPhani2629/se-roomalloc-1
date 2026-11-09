from django.urls import path
from . import views

urlpatterns = [
    path('hostels/', views.hostel_list_view, name='hostel_list'),
    path('hostels/create/', views.hostel_create_view, name='hostel_create'),
    path('hostels/<int:pk>/edit/', views.hostel_update_view, name='hostel_update'),
    path('hostels/<int:pk>/delete/', views.hostel_delete_view, name='hostel_delete'),

    path('rooms/', views.room_list_view, name='room_list'),
    path('rooms/create/', views.room_create_view, name='room_create'),
    path('rooms/<int:pk>/edit/', views.room_update_view, name='room_update'),
    path('rooms/<int:pk>/delete/', views.room_delete_view, name='room_delete'),
]
