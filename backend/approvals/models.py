"""申请单模型。"""

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class ApprovalRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        IN_REVIEW = "in_review", "审批中"
        APPROVED = "approved", "已通过"
        REJECTED = "rejected", "已驳回"

    title = models.CharField("标题", max_length=100)
    content = models.TextField("内容", max_length=2000)
    status = models.CharField(
        "状态",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="approval_requests",
        verbose_name="申请人",
    )
    first_approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="first_approval_requests",
        verbose_name="一级审批人",
    )
    second_approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="second_approval_requests",
        verbose_name="二级审批人",
    )
    current_step = models.PositiveSmallIntegerField(
        "当前步骤",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    submitted_at = models.DateTimeField("提交时间", null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.CheckConstraint(
                condition=~Q(first_approver=F("applicant")),
                name="approval_request_first_approver_not_applicant",
            ),
            models.CheckConstraint(
                condition=~Q(second_approver=F("applicant")),
                name="approval_request_second_approver_not_applicant",
            ),
            models.CheckConstraint(
                condition=Q(current_step__in=[1, 2]) | Q(current_step__isnull=True),
                name="approval_request_current_step_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["applicant", "-created_at"],
                name="approval_applicant_created_idx",
            ),
            models.Index(
                fields=["status", "-created_at"],
                name="approval_status_created_idx",
            ),
        ]

    @property
    def current_approver(self):
        if self.status != self.Status.IN_REVIEW:
            return None
        if self.current_step == 1:
            return self.first_approver
        if self.current_step == 2:
            return self.second_approver
        return None

    def __str__(self):
        return f"{self.title} ({self.status})"
