from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

class APIKeyMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Only require API key if the view is decorated with @api_key
        if getattr(view_func, 'require_api_key', False):
            api_key = request.headers.get('X-API-KEY')
            if not api_key or api_key not in settings.API_KEYS:
                return JsonResponse({'error': 'Unauthorized, connect to X-API-KEY.'}, status=401)
        return None
