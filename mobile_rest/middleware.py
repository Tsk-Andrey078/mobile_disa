from sentry_sdk import capture_exception
from django.http import JsonResponse


class SentryExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception as e:
            capture_exception(e)  # Отправить исключение в Sentry
            raise e  # Перебросить исключение дальше
        return response
