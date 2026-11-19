"""
URL configuration for hostel_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Health check for AWS/Kubernetes/Render/Railway orchestrators
    path('health/', views.health_check_view, name='health_check'),
    
    # Public & Compliance Pages
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('privacy/', views.privacy_policy_view, name='privacy_policy'),
    path('style-guide/', TemplateView.as_view(template_name='style_guide.html'), name='style_guide'),

    # Admin Panel
    path('admin/', admin.site.urls),

    # Application Modules
    path('accounts/', include('accounts.urls')),
    path('hostels/', include('hostels.urls')),
    path('applications/', include('applications.urls')),
    path('allocations/', include('allocations.urls')),
    path('fees/', include('fees.urls')),
    path('complaints/', include('complaints.urls')),
    path('notifications/', include('notifications.urls')),
    path('reports/', include('reports.urls')),
    path('maintenance/', include('maintenance.urls')),
    path('mess/', include('mess.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Global Production Error Handlers
handler400 = 'hostel_project.views.handler400'
handler403 = 'hostel_project.views.handler403'
handler404 = 'hostel_project.views.handler404'
handler500 = 'hostel_project.views.handler500'
