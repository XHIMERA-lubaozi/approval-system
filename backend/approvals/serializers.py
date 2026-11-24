"""申请单序列化器。"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from approvals.models import ApprovalRequest, OperationHistory
from users.serializers import UserSerializer


User = get_user_model()


class DraftInputSerializer(serializers.Serializer):
    """创建和完整更新草稿时使用。"""

    title = serializers.CharField(
        max_length=100,
        trim_whitespace=False,
        error_messages={
            "blank": "请输入标题",
            "max_length": "标题不能超过 100 个字符",
        },
    )
    content = serializers.CharField(
        max_length=2000,
        trim_whitespace=False,
        error_messages={
            "blank": "请输入内容",
            "max_length": "内容不能超过 2000 个字符",
        },
    )
    first_approver_id = serializers.PrimaryKeyRelatedField(
        source="first_approver",
        queryset=User.objects.all(),
        error_messages={
            "does_not_exist": "一级审批人不存在",
            "incorrect_type": "一级审批人不存在",
        },
    )
    second_approver_id = serializers.PrimaryKeyRelatedField(
        source="second_approver",
        queryset=User.objects.all(),
        error_messages={
            "does_not_exist": "二级审批人不存在",
            "incorrect_type": "二级审批人不存在",
        },
    )

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("标题不能仅包含空白")
        return value.strip()

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("内容不能仅包含空白")
        return value

    def validate(self, attrs):
        applicant = (
            self.instance.applicant
            if self.instance is not None
            else self.context["request"].user
        )
        if attrs["first_approver"] == applicant:
            raise serializers.ValidationError(
                {"first_approver_id": ["不能选择自己作为审批人"]}
            )
        if attrs["second_approver"] == applicant:
            raise serializers.ValidationError(
                {"second_approver_id": ["不能选择自己作为审批人"]}
            )
        return attrs

    def create(self, validated_data):
        return ApprovalRequest.objects.create(
            applicant=self.context["request"].user,
            status=ApprovalRequest.Status.DRAFT,
            current_step=None,
            submitted_at=None,
            **validated_data,
        )

    def update(self, instance, validated_data):
        instance.title = validated_data["title"]
        instance.content = validated_data["content"]
        instance.first_approver = validated_data["first_approver"]
        instance.second_approver = validated_data["second_approver"]
        instance.save()
        return instance


class ApprovalRequestSerializer(serializers.ModelSerializer):
    applicant = UserSerializer(read_only=True)
    first_approver = UserSerializer(read_only=True)
    second_approver = UserSerializer(read_only=True)
    current_approver = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalRequest
        fields = (
            "id",
            "title",
            "content",
            "status",
            "applicant",
            "first_approver",
            "second_approver",
            "current_step",
            "current_approver",
            "created_at",
            "updated_at",
            "submitted_at",
        )
        read_only_fields = fields

    def get_current_approver(self, obj):
        approver = obj.current_approver
        return UserSerializer(approver).data if approver else None


class OperationHistorySerializer(serializers.ModelSerializer):
    operator = UserSerializer(read_only=True)
    request_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = OperationHistory
        fields = ('id', 'request_id', 'operator', 'action', 'step', 'comment', 'before_status', 'before_step', 'after_status', 'after_step', 'operated_at')


class ApproveInputSerializer(serializers.Serializer):
    expected_step = serializers.ChoiceField(choices=(1, 2))
    comment = serializers.CharField(required=False, allow_blank=True, max_length=500, trim_whitespace=False)


class RejectInputSerializer(serializers.Serializer):
    expected_step = serializers.ChoiceField(choices=(1, 2))
    comment = serializers.CharField(max_length=500, trim_whitespace=True)


class ApprovalRequestDetailSerializer(ApprovalRequestSerializer):
    history = serializers.SerializerMethodField()

    class Meta(ApprovalRequestSerializer.Meta):
        fields = ApprovalRequestSerializer.Meta.fields + ("history",)

    def get_history(self, obj):
        return OperationHistorySerializer(obj.history.select_related("operator").all(), many=True).data


class RequestListQuerySerializer(serializers.Serializer):
    scope = serializers.ChoiceField(
        choices=("mine", "pending"),
        default="mine",
        error_messages={"invalid_choice": "scope 仅支持 mine 或 pending"},
    )
    page = serializers.IntegerField(
        min_value=1,
        default=1,
        error_messages={"min_value": "page 必须大于等于 1"},
    )
    pageSize = serializers.IntegerField(
        min_value=1,
        max_value=100,
        default=10,
        error_messages={
            "min_value": "pageSize 必须大于等于 1",
            "max_value": "pageSize 不能超过 100",
        },
    )
    status = serializers.ChoiceField(
        choices=ApprovalRequest.Status.choices,
        required=False,
        error_messages={"invalid_choice": "status 不是有效的申请状态"},
    )
    keyword = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
        trim_whitespace=True,
        error_messages={"max_length": "关键词不能超过 100 个字符"},
    )
