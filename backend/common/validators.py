"""项目自定义的密码校验器。"""

import re

from django.contrib.auth.password_validation import UserAttributeSimilarityValidator
from django.core.exceptions import ValidationError


class CharacterTypeValidator:
    """要求密码至少包含大写字母、小写字母、数字、符号中的两类。"""

    def validate(self, password, user=None):
        types = (
            bool(re.search(r"[a-z]", password)),
            bool(re.search(r"[A-Z]", password)),
            bool(re.search(r"\d", password)),
            bool(re.search(r"[^A-Za-z0-9]", password)),
        )
        if sum(types) < 2:
            raise ValidationError(
                "密码至少包含大写字母、小写字母、数字、符号中的两类。",
                code="password_too_simple",
            )

    def get_help_text(self):
        return "密码至少包含大写字母、小写字母、数字、符号中的两类。"


class AccountSimilarityValidator(UserAttributeSimilarityValidator):
    """沿用 Django 的相似度规则，将提示中的“用户名”统一为“账号”。"""

    def get_error_message(self):
        return "密码与账号过于相似。"
