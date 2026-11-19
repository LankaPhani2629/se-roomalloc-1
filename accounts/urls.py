from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('staff-login/', views.staff_login_view, name='staff_login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('dashboard-redirect/', views.dashboard_redirect_view, name='dashboard_redirect'),
    path('profile/export/', views.student_data_export_view, name='student_data_export'),

    # Secure Cryptographic Password Reset Flow
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset_form.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset'
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm'
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    # Staff Admin Operations
    path('admin/students/', views.admin_student_list_view, name='admin_student_list'),
    path('admin/staff/', views.admin_staff_list_view, name='admin_staff_list'),
    path('admin/staff/add/', views.admin_add_staff_view, name='admin_staff_add'),
    path('admin/staff/<int:user_id>/toggle-status/', views.admin_staff_toggle_active_view, name='admin_staff_toggle_active'),
    path('admin/staff/<int:user_id>/reset-password/', views.admin_staff_reset_password_view, name='admin_staff_reset_password'),
    path('admin/staff/<int:user_id>/reassign/', views.admin_staff_reassign_view, name='admin_staff_reassign'),
]
