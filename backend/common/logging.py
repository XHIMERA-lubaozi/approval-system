"""日志脱敏工具。

日志中不得出现密码、密码哈希、JWT、Authorization 请求头、完整请求体或数据库连接凭据。
统一在格式化阶段做一次兜底替换，避免调用方遗漏。
"""

import logging
import re


_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{4,}\.[A-Za-z0-9_-]{4,}\.[A-Za-z0-9_-]{4,}\b")
_AUTHORIZATION_RE = re.compile(
    r"(?i)\b(authorization)(\s*[:=]\s*)(?:bearer\s+)?[^\s,;\"']+"
)
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_SECRET_PAIR_RE = re.compile(
    r"(?i)([\"']?(?:password|passwd|pwd|password_hash|secret|secret_key|"
    r"access_token|refresh_token|token)[\"']?\s*[:=]\s*)"
    r"(\"[^\"]*\"|'[^']*'|[^\s,;}\]]+)"
)
_FORM_SECRET_RE = re.compile(r"(?i)((?:password|passwd|pwd|token|access_token)=)[^&\s]+")
_PASSWORD_HASH_RE = re.compile(
    r"\b(?:pbkdf2_(?:sha1|sha256)|argon2\w*|bcrypt(?:_sha256)?|scrypt)\$[^\s\"',;]+"
)

_REDACTED = "[REDACTED]"


def configured_secrets():
    """返回需要从日志中抹除的配置值（签名密钥、数据库密码）。"""

    try:
        from django.conf import settings

        candidates = [getattr(settings, "SECRET_KEY", "")]
        database = getattr(settings, "DATABASES", {}).get("default", {})
        candidates.append(database.get("PASSWORD", ""))
        return tuple(
            str(value) for value in candidates if value and len(str(value)) >= 4
        )
    except Exception:  # pragma: no cover - settings 尚未就绪时保持日志可用
        return ()


def redact_text(text, secrets=None):
    """对一段文本做脱敏，返回可安全写入日志的内容。"""

    if not text:
        return text

    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")

    for secret in secrets if secrets is not None else configured_secrets():
        if secret and len(secret) >= 4:
            text = text.replace(secret, _REDACTED)

    text = _AUTHORIZATION_RE.sub(r"\1\2" + _REDACTED, text)
    text = _SECRET_PAIR_RE.sub(r"\1" + _REDACTED, text)
    text = _FORM_SECRET_RE.sub(r"\1" + _REDACTED, text)
    text = _BEARER_RE.sub("Bearer " + _REDACTED, text)
    text = _JWT_RE.sub(_REDACTED, text)
    text = _PASSWORD_HASH_RE.sub(_REDACTED, text)
    return text


class RedactingFormatter(logging.Formatter):
    """在输出前对完整日志（含堆栈）做脱敏的格式化器。"""

    def format(self, record):
        return redact_text(super().format(record))
