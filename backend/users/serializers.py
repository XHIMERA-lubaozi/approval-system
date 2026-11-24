"""用户与认证相关序列化器。"""

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from common.exceptions import InvalidCredentials


User = get_user_model()

DUPLICATE_USERNAME_MESSAGE = "该账号已被注册"


class UserSerializer(serializers.ModelSerializer):
    """对外暴露的用户摘要，仅包含契约中的三个字段。"""

    class Meta:
        model = User
        fields = ("id", "username", "display_name")
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        validators=[UnicodeUsernameValidator()],
        error_messages={"blank": "请输入账号"},
    )
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        error_messages={"blank": "请输入密码"},
    )
    display_name = serializers.CharField(
        max_length=150,
        error_messages={"blank": "请输入昵称"},
    )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(DUPLICATE_USERNAME_MESSAGE)
        return value

    def validate_display_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("请输入昵称")
        return value

    def validate(self, attrs):
        candidate = User(
            username=attrs.get("username", ""),
            display_name=attrs.get("display_name", ""),
        )
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return User.objects.create_user(**validated_data)
        except IntegrityError as exc:
            # 并发注册时序列化器的存在性检查可能同时通过，由数据库唯一约束兜底。
            raise serializers.ValidationError(
                {"username": [DUPLICATE_USERNAME_MESSAGE]}
            ) from exc


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        error_messages={"blank": "请输入账号"},
    )
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        error_messages={"blank": "请输入密码"},
    )

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["username"],
            password=attrs["password"],
        )
        if user is None:
            # 用户不存在与密码错误使用同一提示，避免枚举账号。
            raise InvalidCredentials()
        attrs["user"] = user
        return attrs
