from django.urls import path
from . import views

urlpatterns = [
    # Dashboards
    path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),
    path('dashboard/warden/', views.warden_dashboard_view, name='warden_dashboard'),
    path('dashboard/student/', views.student_dashboard_view, name='student_dashboard'),
    path('dashboard/accountant/', views.accountant_dashboard_view, name='accountant_dashboard'),

    # Reports
    path('hub/', views.reports_hub_view, name='reports_hub'),
    path('occupancy/', views.occupancy_report_view, name='occupancy_report'),
    path('vacancy/', views.vacancy_report_view, name='vacancy_report'),
    path('allocations/', views.allocation_list_report_view, name='allocation_report'),
    path('fee-dues/', views.fee_dues_report_view, name='fee_dues_report'),
    path('complaints/', views.complaints_report_view, name='complaints_report'),
]

