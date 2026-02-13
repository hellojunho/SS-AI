from django.http import JsonResponse

from .logging_utils import log_error


class ExceptionLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        log_error(request, exception, status_code=500)
        return JsonResponse({"detail": "Internal Server Error"}, status=500)
