"""注册、登录与当前用户接口测试。"""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from users.serializers import RegisterSerializer


User = get_user_model()

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
ME_URL = "/api/users/me"

VALID_PAYLOAD = {
    "username": "alice01",
    "password": "Str0ng-Passw0rd!",
    "display_name": "Alice",
}


class RegisterApiTests(APITestCase):
    def test_register_returns_created_summary_and_hashes_password(self):
        response = self.client.post(REGISTER_URL, VALID_PAYLOAD, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(set(response.data), {"id", "username", "display_name"})
        self.assertEqual(response.data["username"], "alice01")
        self.assertEqual(response.data["display_name"], "Alice")
        self.assertNotIn("password", response.data)

        user = User.objects.get(username="alice01")
        self.assertTrue(user.password.startswith("pbkdf2_sha256$"))
        self.assertNotEqual(user.password, VALID_PAYLOAD["password"])
        self.assertTrue(user.check_password(VALID_PAYLOAD["password"]))

    def test_register_allows_anonymous_access_without_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")

        response = self.client.post(REGISTER_URL, VALID_PAYLOAD, format="json")

        self.assertEqual(response.status_code, 201)

    def test_register_rejects_duplicate_username_with_field_error(self):
        User.objects.create_user(
            username="alice01",
            password="Str0ng-Passw0rd!",
            display_name="Alice",
        )

        with self.assertNoLogs("common.exceptions", level="ERROR"):
            response = self.client.post(REGISTER_URL, VALID_PAYLOAD, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "validation_error")
        self.assertIn("username", response.data["details"])
        self.assertIn("已被注册", str(response.data["details"]["username"]))

    def test_register_requires_all_fields(self):
        response = self.client.post(REGISTER_URL, {}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "validation_error")
        self.assertEqual(
            set(response.data["details"]), {"username", "password", "display_name"}
        )

    def test_register_rejects_blank_display_name(self):
        payload = {**VALID_PAYLOAD, "display_name": "   "}

        response = self.client.post(REGISTER_URL, payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("display_name", response.data["details"])
        self.assertIn("昵称", str(response.data["details"]["display_name"]))

    def test_register_requires_at_least_two_character_types(self):
        payload = {**VALID_PAYLOAD, "password": "abcdefgh"}

        response = self.client.post(REGISTER_URL, payload, format="json")

        self.assertEqual(response.status_code, 400)
        messages = " ".join(response.data["details"]["password"])
        self.assertIn("两类", messages)
        self.assertFalse(User.objects.filter(username="alice01").exists())

    def test_register_enforces_configured_password_rules(self):
        payload = {**VALID_PAYLOAD, "password": "12345678"}

        response = self.client.post(REGISTER_URL, payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.data["details"])
        self.assertFalse(User.objects.filter(username="alice01").exists())

    def test_password_similarity_message_uses_account_wording(self):
        payload = {**VALID_PAYLOAD, "password": "alice01!"}

        response = self.client.post(REGISTER_URL, payload, format="json")

        self.assertEqual(response.status_code, 400)
        messages = " ".join(response.data["details"]["password"])
        self.assertIn("账号", messages)
        self.assertNotIn("用户名", messages)

    def test_register_handles_unique_race_via_database_constraint(self):
        """模拟存在性检查通过后另一请求先完成注册的并发窗口。"""

        User.objects.create_user(
            username="alice01",
            password="Str0ng-Passw0rd!",
            display_name="Alice",
        )

        with patch("users.serializers.User.objects.filter") as filter_mock:
            filter_mock.return_value.exists.return_value = False
            response = self.client.post(REGISTER_URL, VALID_PAYLOAD, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "validation_error")
        self.assertIn("已被注册", str(response.data["details"]["username"]))

    def test_database_unique_constraint_rejects_duplicate_rows(self):
        User.objects.create_user(
            username="alice01",
            password="Str0ng-Passw0rd!",
            display_name="Alice",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(
                    username="alice01",
                    password="Another-Passw0rd!",
                    display_name="Another Alice",
                )


class LoginApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice01",
            password="Str0ng-Passw0rd!",
            display_name="Alice",
        )

    def test_login_returns_bearer_access_token(self):
        response = self.client.post(
            LOGIN_URL,
            {"username": "alice01", "password": "Str0ng-Passw0rd!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {"access_token", "token_type"})
        self.assertEqual(response.data["token_type"], "Bearer")
        self.assertTrue(response.data["access_token"])

        token = AccessToken(response.data["access_token"])
        self.assertEqual(int(token["user_id"]), self.user.pk)

    def test_login_allows_anonymous_access_without_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")

        response = self.client.post(
            LOGIN_URL,
            {"username": "alice01", "password": "Str0ng-Passw0rd!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

    def test_login_rejects_wrong_password_and_unknown_user(self):
        cases = (
            {"username": "alice01", "password": "wrong-password"},
            {"username": "nobody", "password": "Str0ng-Passw0rd!"},
        )

        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertNoLogs("common.exceptions", level="ERROR"):
                    response = self.client.post(LOGIN_URL, payload, format="json")

                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.data["code"], "invalid_credentials")
                self.assertEqual(response.data["message"], "账号或密码错误")

    def test_login_requires_credentials(self):
        response = self.client.post(LOGIN_URL, {}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "validation_error")
        self.assertEqual(set(response.data["details"]), {"username", "password"})


class CurrentUserApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice01",
            password="Str0ng-Passw0rd!",
            display_name="Alice",
        )

    def _auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_me_returns_current_user(self):
        self._auth(AccessToken.for_user(self.user))

        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {"id": self.user.pk, "username": "alice01", "display_name": "Alice"},
        )

    def test_me_requires_token(self):
        with self.assertNoLogs("common.exceptions", level="ERROR"):
            response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], "unauthorized")
        self.assertTrue(response.data["message"])

    def test_me_rejects_invalid_token(self):
        self._auth("not-a-valid-token")

        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], "unauthorized")

    def test_me_rejects_expired_token(self):
        token = AccessToken.for_user(self.user)
        token.set_exp(
            from_time=timezone.now() - timedelta(minutes=10),
            lifetime=timedelta(minutes=5),
        )
        self._auth(str(token))

        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], "unauthorized")


class UnexpectedErrorTests(APITestCase):
    def test_unexpected_error_returns_500_and_writes_redacted_log(self):
        leaked_password = "super-secret-value"
        leaked_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0In0.c2lnbmF0dXJlMTIzNDU2"
        error = RuntimeError(
            f"database failed password={leaked_password} Authorization: Bearer {leaked_jwt}"
        )

        with patch.object(RegisterSerializer, "create", side_effect=error):
            with self.assertLogs("common.exceptions", level="ERROR") as captured:
                response = self.client.post(REGISTER_URL, VALID_PAYLOAD, format="json")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data,
            {"code": "internal_error", "message": "服务器内部错误，请稍后重试"},
        )

        output = "\n".join(captured.output)
        self.assertIn("method=POST", output)
        self.assertIn("path=/api/auth/register", output)
        self.assertIn("RuntimeError", output)
        self.assertNotIn(leaked_password, output)
        self.assertNotIn(leaked_jwt, output)
        self.assertNotIn("Authorization: Bearer", output)
        self.assertNotIn("pbkdf2_sha256$", output)
