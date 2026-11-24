"""DRF 统一异常处理。

成功响应由各视图返回；所有非 2xx 响应统一为 ``{code, message, details?}``。
预期失败（参数错误、凭据错误、认证失败等）返回可读的 4xx，不记录堆栈；
未预期异常记录一条脱敏后的 ERROR 日志，并向客户端返回通用 500 提示。
"""

import logging
import traceback

from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from common.logging import redact_text


logger = logging.getLogger("common.exceptions")

GENERIC_500_MESSAGE = "服务器内部错误，请稍后重试"


class InvalidCredentials(exceptions.APIException):
    """登录账号或密码错误。"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "账号或密码错误"
    default_code = "invalid_credentials"


def _normalise(value):
    if isinstance(value, dict):
        return {str(key): _normalise(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalise(item) for item in value]
    return str(value)


def _details_from(detail):
    if isinstance(detail, dict):
        return {str(key): _normalise(value) for key, value in detail.items()}
    if isinstance(detail, (list, tuple)):
        return {"non_field_errors": _normalise(detail)}
    return None


def _code_for(exc, response):
    if isinstance(exc, exceptions.ValidationError):
        return "validation_error"
    if isinstance(exc, (exceptions.NotAuthenticated, exceptions.AuthenticationFailed)):
        return "unauthorized"
    if isinstance(exc, exceptions.PermissionDenied):
        return "forbidden"
    if isinstance(exc, (Http404, exceptions.NotFound)):
        return "not_found"
    if isinstance(exc, exceptions.MethodNotAllowed):
        return "method_not_allowed"
    if isinstance(exc, exceptions.UnsupportedMediaType):
        return "unsupported_media_type"
    if isinstance(exc, exceptions.Throttled):
        return "too_many_requests"
    if isinstance(exc, exceptions.ParseError):
        return "invalid_request"
    if isinstance(exc, exceptions.APIException):
        code = getattr(exc, "default_code", None)
        if code and code != "error":
            return str(code)
    return f"http_{response.status_code}"


def _message_for(exc, response):
    if isinstance(exc, exceptions.ValidationError):
        return "参数校验失败"
    if isinstance(exc, (exceptions.NotAuthenticated, exceptions.AuthenticationFailed)):
        return "未登录或登录已失效，请重新登录"
    if isinstance(exc, exceptions.PermissionDenied):
        return "没有操作权限"
    if isinstance(exc, (Http404, exceptions.NotFound)):
        return "请求的资源不存在"
    if isinstance(exc, exceptions.MethodNotAllowed):
        return "请求方法不被允许"
    if isinstance(exc, exceptions.UnsupportedMediaType):
        return "请求内容类型不受支持"
    if isinstance(exc, exceptions.Throttled):
        return "请求过于频繁，请稍后再试"
    if isinstance(exc, exceptions.ParseError):
        return "请求体格式不正确"

    detail = getattr(response, "data", None)
    if isinstance(detail, str) and detail:
        return detail
    if isinstance(detail, dict) and set(detail) == {"detail"}:
        message = detail["detail"]
        if isinstance(message, str) and message:
            return message
    return "请求无法处理"


def exception_handler(exc, context):
    """替换 DRF 默认异常处理，输出统一错误结构并记录未预期异常。"""

    response = drf_exception_handler(exc, context)

    if response is None:
        request = context.get("request")
        method = getattr(request, "method", "-")
        path = getattr(request, "path", "-")
        stack = redact_text(traceback.format_exc())
        logger.error(
            "未处理异常 method=%s path=%s exception=%s\n%s",
            method,
            path,
            type(exc).__name__,
            stack,
        )
        return Response(
            {"code": "internal_error", "message": GENERIC_500_MESSAGE},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    payload = {"code": _code_for(exc, response), "message": _message_for(exc, response)}
    if isinstance(exc, exceptions.ValidationError):
        details = _details_from(getattr(response, "data", None))
        if details:
            payload["details"] = details

    handled = Response(payload, status=response.status_code)
    for header, value in response.headers.items():
        if header.lower() not in ("content-type", "content-length"):
            handled[header] = value
    return handled
