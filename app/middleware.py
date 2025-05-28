from django.conf import settings
from django.http import JsonResponse


class APIKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        api_key = request.headers.get('X-API-KEY')

        if not api_key or api_key not in settings.FRONTEND_API_KEYS:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        return self.get_response(request)
