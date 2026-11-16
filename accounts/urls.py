from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('staff-login/', views.staff_login_view, name='staff_login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('dashboard-redirect/', views.dashboard_redirect_view, name='dashboard_redirect'),
    path('admin/students/', views.admin_student_list_view, name='admin_student_list'),
    path('admin/staff/', views.admin_staff_list_view, name='admin_staff_list'),
    path('admin/staff/add/', views.admin_add_staff_view, name='admin_staff_add'),
    path('admin/staff/<int:user_id>/toggle-status/', views.admin_staff_toggle_active_view, name='admin_staff_toggle_active'),
    path('admin/staff/<int:user_id>/reset-password/', views.admin_staff_reset_password_view, name='admin_staff_reset_password'),
    path('admin/staff/<int:user_id>/reassign/', views.admin_staff_reassign_view, name='admin_staff_reassign'),
]

