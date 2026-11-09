from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('dashboard-redirect/', views.dashboard_redirect_view, name='dashboard_redirect'),
    path('admin/students/', views.admin_student_list_view, name='admin_student_list'),
]
