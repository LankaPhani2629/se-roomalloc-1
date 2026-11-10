from django.urls import path
from . import views

urlpatterns = [
    path('student/', views.student_complaints_view, name='student_complaints'),
    path('warden/', views.warden_complaints_view, name='warden_complaints'),
    path('warden/<int:pk>/update/', views.warden_complaint_update_view, name='warden_complaint_update'),
]

