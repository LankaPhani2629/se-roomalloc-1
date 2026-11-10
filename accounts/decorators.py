from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin


def role_required(*allowed_roles):
    """
    Decorator for views that checks whether a user has one of the allowed roles.
    Raises PermissionDenied (403) or redirects to login if unauthenticated.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have permission to access this page.")
        return _wrapped_view
    return decorator


def admin_required(view_func):
    return role_required('ADMIN')(view_func)


def warden_required(view_func):
    return role_required('WARDEN', 'ADMIN')(view_func)


def student_required(view_func):
    return role_required('STUDENT')(view_func)


def accountant_required(view_func):
    return role_required('ACCOUNTANT', 'ADMIN')(view_func)


class RoleRequiredMixin(AccessMixin):
    """CBV mixin that verifies user has required role."""
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or request.user.role in self.allowed_roles):
            raise PermissionDenied("You do not have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)

