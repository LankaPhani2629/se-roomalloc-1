from django.urls import path
from . import views

urlpatterns = [
    path('rules/', views.allocation_rules_view, name='allocation_rules'),
    path('rules/<int:pk>/delete/', views.delete_allocation_rule_view, name='delete_allocation_rule'),
    path('auto-allocate/', views.run_auto_allocation_view, name='run_auto_allocation'),
    path('manual-allocate/', views.manual_allocation_view, name='manual_allocation'),
    path('results/', views.allocation_results_view, name='allocation_results'),

    # Student room detail & requests
    path('my-room/', views.student_room_detail_view, name='student_room_detail'),
    path('requests/', views.student_room_requests_view, name='student_room_requests'),

    # Warden review
    path('warden/requests/', views.warden_room_requests_view, name='warden_room_requests'),
    path('warden/requests/<int:pk>/process/', views.warden_process_request_view, name='warden_process_request'),
]

