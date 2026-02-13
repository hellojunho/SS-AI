from rest_framework.views import exception_handler

from .logging_utils import log_error


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request = context.get("request")
    if response is not None and request is not None:
        log_error(request, exc, status_code=response.status_code)
    return response
