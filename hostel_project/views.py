import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.db import connection
from django.core.cache import cache

logger = logging.getLogger('django')


def health_check_view(request):
    """
    Production health check endpoint for load balancers and orchestrators.
    Verifies database connectivity and cache responsiveness.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'services': {}
    }
    http_code = 200

    # 1. Check Database Connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            if row and row[0] == 1:
                health_status['services']['database'] = 'connected'
            else:
                health_status['services']['database'] = 'unexpected_response'
                health_status['status'] = 'degraded'
                http_code = 503
    except Exception as e:
        logger.error(f"Health check DB failure: {e}")
        health_status['services']['database'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'
        http_code = 503

    # 2. Check Cache
    try:
        cache.set('__health_probe__', 'ok', timeout=10)
        probe_val = cache.get('__health_probe__')
        if probe_val == 'ok':
            health_status['services']['cache'] = 'connected'
        else:
            health_status['services']['cache'] = 'unresponsive'
    except Exception as e:
        health_status['services']['cache'] = f'error: {str(e)}'

    return JsonResponse(health_status, status=http_code)


def privacy_policy_view(request):
    """Public GDPR-compliant data privacy policy page."""
    return render(request, 'privacy_policy.html')


# Custom Production Error Handlers
def handler400(request, exception=None):
    return render(request, '400.html', status=400)


def handler403(request, exception=None):
    return render(request, '403.html', {'message': str(exception) if exception else ''}, status=403)


def handler404(request, exception=None):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)
