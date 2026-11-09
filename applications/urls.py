from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.student_profile_view, name='student_profile'),
    path('apply/', views.apply_room_view, name='apply_room'),
    path('status/', views.student_application_status_view, name='student_application_status'),
    path('warden/applications/', views.warden_applications_view, name='warden_applications'),
    path('warden/applications/<int:pk>/review/', views.warden_application_review_view, name='warden_application_review'),
    path('admin/periods/', views.application_periods_view, name='application_periods'),
]
