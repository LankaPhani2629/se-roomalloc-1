"""
URL configuration for hostel_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('style-guide/', TemplateView.as_view(template_name='style_guide.html'), name='style_guide'),
    path('accounts/', include('accounts.urls')),
    path('hostels/', include('hostels.urls')),
    path('applications/', include('applications.urls')),
    path('allocations/', include('allocations.urls')),
    path('fees/', include('fees.urls')),
    path('complaints/', include('complaints.urls')),
    path('notifications/', include('notifications.urls')),
    path('reports/', include('reports.urls')),
]
