"""日志脱敏格式化器测试。"""

import logging

from django.test import SimpleTestCase

from common.logging import RedactingFormatter, redact_text


class RedactionTests(SimpleTestCase):
    def test_redact_text_removes_credentials(self):
        text = (
            "Authorization: Bearer abc.def.ghi password=hunter2 "
            "access_token=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2ln "
            'pbkdf2_sha256$600000$salt$hash "password": "another-secret"'
        )

        redacted = redact_text(text, secrets=("db-password-value",))

        for secret in ("hunter2", "eyJhbGciOiJIUzI1NiJ9", "pbkdf2_sha256$", "another-secret"):
            self.assertNotIn(secret, redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_formatter_redacts_exception_traceback(self):
        formatter = RedactingFormatter("%(message)s")
        try:
            raise RuntimeError("password=top-secret token=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2ln")
        except RuntimeError:
            import sys

            record = logging.LogRecord(
                "common.exceptions",
                logging.ERROR,
                __file__,
                1,
                "未处理异常",
                (),
                sys.exc_info(),
            )

        formatted = formatter.format(record)

        self.assertIn("RuntimeError", formatted)
        self.assertNotIn("top-secret", formatted)
        self.assertNotIn("eyJhbGciOiJIUzI1NiJ9", formatted)
