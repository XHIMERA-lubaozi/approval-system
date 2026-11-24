"""待我审批列表（scope=pending）的筛选、排序与分页测试。"""

from datetime import timedelta

from django.utils import timezone

from approvals.models import ApprovalRequest
from approvals.tests.test_drafts import REQUESTS_URL, DraftApiTestCase


PENDING_SCOPE = "pending"


class PendingScopeTests(DraftApiTestCase):
    """通过 HTTP 接口验证待办范围，并回查数据库确认状态。"""

    def submit(self, obj, applicant=None):
        self.client.force_authenticate(user=applicant or obj.applicant)
        response = self.client.post(self.request_detail_url(obj.pk) + "/submit")
        self.assertEqual(response.status_code, 200, response.data)
        obj.refresh_from_db()
        return obj

    def approve(self, obj, user, expected_step):
        self.client.force_authenticate(user=user)
        response = self.client.post(
            self.request_detail_url(obj.pk) + "/approve",
            {"expected_step": expected_step},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        obj.refresh_from_db()
        return obj

    def create_in_review(self, *, applicant=None, first=None, second=None, title="测试申请", step=1):
        """创建并提交申请；step=2 时先由一级审批人通过，使申请停在二级。"""
        obj = self.create_request(
            applicant=applicant,
            first=first,
            second=second,
            title=title,
        )
        self.submit(obj)
        if step == 2:
            self.approve(obj, obj.first_approver, 1)
        self.assertEqual(obj.status, ApprovalRequest.Status.IN_REVIEW)
        self.assertEqual(obj.current_step, step)
        return obj

    def get_pending(self, user=None, **params):
        self.client.force_authenticate(user=user or self.first)
        params["scope"] = PENDING_SCOPE
        return self.client.get(REQUESTS_URL, params)

    def test_pending_returns_only_requests_waiting_for_current_user(self):
        # 当前待办：一级由 first 处理。
        first_step = self.create_in_review(
            first=self.first, second=self.second, title="一级待办"
        )
        # 当前待办：二级由 first 处理（一级由 second 完成）。
        second_step = self.create_in_review(
            applicant=self.outsider,
            first=self.second,
            second=self.first,
            title="二级待办",
            step=2,
        )
        # 尚未轮到 first：申请停在一级，first 只是二级审批人。
        not_yet = self.create_in_review(
            first=self.outsider, second=self.first, title="尚未轮到"
        )
        # 已由他人处理：first 完成一级后，申请停在 second 之外的审批人。
        handled_by_other = self.create_in_review(
            first=self.first, second=self.outsider, title="他人处理", step=2
        )
        # 草稿与已结束申请由 first 担任审批人，但不属于待办。
        draft = self.create_request(
            first=self.first, second=self.second, title="草稿申请"
        )
        approved = self.create_request(
            first=self.first,
            second=self.second,
            title="已通过申请",
            status=ApprovalRequest.Status.APPROVED,
            submitted_at=timezone.now(),
        )
        rejected = self.create_request(
            first=self.first,
            second=self.second,
            title="已驳回申请",
            status=ApprovalRequest.Status.REJECTED,
            submitted_at=timezone.now(),
        )
        # 他人的待办：避免把别人的待办泄露给 first。
        other_pending = self.create_in_review(
            first=self.second, second=self.outsider, title="二级审批人的待办"
        )
        # 数据异常但数据库约束允许的行：状态不是审批中，即便步骤和审批人匹配也不得进入待办。
        # 用于固定“待办只包含审批中申请”这一条件本身，而不是依赖当前步骤恰好为空。
        inconsistent_draft = self.create_request(
            first=self.first,
            second=self.second,
            title="异常草稿",
            current_step=1,
        )
        inconsistent_finished = self.create_request(
            first=self.second,
            second=self.first,
            title="异常已通过",
            status=ApprovalRequest.Status.APPROVED,
            current_step=2,
            submitted_at=timezone.now(),
        )

        response = self.get_pending(self.first)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(set(ids), {first_step.pk, second_step.pk})
        self.assertEqual(len(ids), 2)
        for item in response.data["results"]:
            self.assertEqual(item["status"], ApprovalRequest.Status.IN_REVIEW)
            self.assertEqual(item["current_approver"]["id"], self.first.pk)
        for excluded in (
            not_yet,
            handled_by_other,
            draft,
            approved,
            rejected,
            other_pending,
            inconsistent_draft,
            inconsistent_finished,
        ):
            self.assertNotIn(excluded.pk, ids)

        # 数据库侧确认：两条申请确实停在 first 需要处理的步骤上。
        self.assertEqual(
            set(
                ApprovalRequest.objects.filter(
                    pk__in=[first_step.pk, second_step.pk]
                ).values_list("current_step", "first_approver_id", "second_approver_id")
            ),
            {(1, self.first.pk, self.second.pk), (2, self.second.pk, self.first.pk)},
        )
        self.assertEqual(
            ApprovalRequest.objects.get(pk=handled_by_other.pk).current_approver,
            self.outsider,
        )

    def test_pending_filters_before_paginating(self):
        matching = [
            self.create_in_review(
                title=f"采购显示器 {index}", first=self.first, second=self.second
            )
            for index in range(6)
        ]
        others = [
            self.create_in_review(
                title=f"差旅报销 {index}", first=self.first, second=self.second
            )
            for index in range(3)
        ]
        # 同关键词但不在待办范围：草稿与他人待办。
        self.create_request(first=self.first, second=self.second, title="采购显示器 草稿")
        self.create_in_review(
            first=self.outsider, second=self.first, title="采购显示器 他人待办"
        )

        pages = [
            self.get_pending(
                self.first,
                page=page,
                pageSize=2,
                status=ApprovalRequest.Status.IN_REVIEW,
                keyword="采购显示器",
            )
            for page in (1, 2, 3)
        ]

        for page in pages:
            self.assertEqual(page.status_code, 200)
            self.assertEqual(page.data["count"], 6)
            self.assertEqual(page.data["page_size"], 2)
            self.assertEqual(len(page.data["results"]), 2)

        ids = [item["id"] for page in pages for item in page.data["results"]]
        self.assertEqual(len(ids), 6)
        self.assertEqual(len(set(ids)), 6)
        self.assertEqual(set(ids), {obj.pk for obj in matching})
        for page in pages:
            for item in page.data["results"]:
                self.assertEqual(item["status"], ApprovalRequest.Status.IN_REVIEW)
                self.assertTrue(item["title"].startswith("采购显示器"))

        # 关键词与状态各自独立生效：换关键词后只统计该关键词的待办。
        second_keyword = self.get_pending(self.first, keyword="差旅报销")
        self.assertEqual(second_keyword.data["count"], 3)
        self.assertEqual(
            {item["id"] for item in second_keyword.data["results"]},
            {obj.pk for obj in others},
        )
        unfiltered = self.get_pending(self.first)
        self.assertEqual(unfiltered.data["count"], 9)

    def test_pending_orders_tied_created_at_by_id_descending_across_pages(self):
        created = [
            self.create_in_review(
                title=f"同秒申请 {index}", first=self.first, second=self.second
            )
            for index in range(5)
        ]
        fixed_time = timezone.now() - timedelta(hours=1)
        ApprovalRequest.objects.filter(pk__in=[obj.pk for obj in created]).update(
            created_at=fixed_time
        )

        pages = [self.get_pending(self.first, page=page, pageSize=2) for page in (1, 2, 3)]

        for page in pages:
            self.assertEqual(page.status_code, 200)
            self.assertEqual(page.data["count"], 5)

        ids = [item["id"] for page in pages for item in page.data["results"]]
        expected = sorted((obj.pk for obj in created), reverse=True)
        self.assertEqual(ids, expected)
        self.assertEqual(len(set(ids)), 5)
        self.assertEqual(
            list(
                ApprovalRequest.objects.order_by("-created_at", "-id").values_list(
                    "id", flat=True
                )
            ),
            expected,
        )
        self.assertEqual(
            ApprovalRequest.objects.filter(pk__in=expected, created_at=fixed_time).count(),
            5,
        )

    def test_invalid_scope_is_rejected(self):
        response = self.client.get(REQUESTS_URL, {"scope": "all"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "validation_error")
        self.assertEqual(
            response.data["details"]["scope"],
            ["scope 仅支持 mine 或 pending"],
        )

    def test_pending_with_non_review_status_returns_empty_result(self):
        pending = self.create_in_review(
            first=self.first, second=self.second, title="真实待办"
        )

        for status_value in (
            ApprovalRequest.Status.DRAFT,
            ApprovalRequest.Status.APPROVED,
            ApprovalRequest.Status.REJECTED,
        ):
            with self.subTest(status=status_value):
                response = self.get_pending(self.first, status=status_value)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["count"], 0)
                self.assertEqual(response.data["results"], [])

        in_review = self.get_pending(self.first, status=ApprovalRequest.Status.IN_REVIEW)
        self.assertEqual(in_review.status_code, 200)
        self.assertEqual(in_review.data["count"], 1)
        self.assertEqual([item["id"] for item in in_review.data["results"]], [pending.pk])
