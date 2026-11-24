"""草稿管理接口测试。"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from approvals.models import ApprovalRequest


User = get_user_model()

REQUESTS_URL = "/api/requests"


class DraftApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.applicant = User.objects.create_user(
            username="applicant",
            password="Str0ng-Passw0rd!",
            display_name="申请人",
        )
        cls.first = User.objects.create_user(
            username="first",
            password="Str0ng-Passw0rd!",
            display_name="一级审批人",
        )
        cls.second = User.objects.create_user(
            username="second",
            password="Str0ng-Passw0rd!",
            display_name="二级审批人",
        )
        cls.outsider = User.objects.create_user(
            username="outsider",
            password="Str0ng-Passw0rd!",
            display_name="无关用户",
        )

    def setUp(self):
        self.client.force_authenticate(user=self.applicant)

    def payload(self, **overrides):
        data = {
            "title": "采购申请",
            "content": "需要采购两台显示器。",
            "first_approver_id": self.first.pk,
            "second_approver_id": self.second.pk,
        }
        data.update(overrides)
        return data

    def create_request(self, applicant=None, first=None, second=None, **overrides):
        applicant = applicant or self.applicant
        first = first or self.first
        second = second or self.second
        values = {
            "title": "测试申请",
            "content": "测试内容",
            "status": ApprovalRequest.Status.DRAFT,
            "applicant": applicant,
            "first_approver": first,
            "second_approver": second,
            "current_step": None,
            "submitted_at": None,
        }
        values.update(overrides)
        return ApprovalRequest.objects.create(**values)

    def request_detail_url(self, request_id):
        return f"{REQUESTS_URL}/{request_id}"


class CreateDraftTests(DraftApiTestCase):
    def test_create_draft_uses_current_user_and_initial_state(self):
        response = self.client.post(REQUESTS_URL, self.payload(), format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "draft")
        self.assertIsNone(response.data["current_step"])
        self.assertIsNone(response.data["current_approver"])
        self.assertIsNone(response.data["submitted_at"])
        self.assertEqual(response.data["applicant"]["id"], self.applicant.pk)
        self.assertEqual(response.data["first_approver"]["id"], self.first.pk)
        self.assertEqual(response.data["second_approver"]["id"], self.second.pk)

        approval_request = ApprovalRequest.objects.get(pk=response.data["id"])
        self.assertEqual(approval_request.applicant, self.applicant)
        self.assertEqual(approval_request.status, ApprovalRequest.Status.DRAFT)
        self.assertIsNone(approval_request.current_step)
        self.assertIsNone(approval_request.submitted_at)

    def test_create_ignores_server_managed_fields(self):
        payload = self.payload(
            status="approved",
            applicant=self.outsider.pk,
            current_step=2,
            submitted_at="2020-01-01T00:00:00Z",
        )

        response = self.client.post(REQUESTS_URL, payload, format="json")

        self.assertEqual(response.status_code, 201)
        approval_request = ApprovalRequest.objects.get(pk=response.data["id"])
        self.assertEqual(approval_request.applicant, self.applicant)
        self.assertEqual(approval_request.status, ApprovalRequest.Status.DRAFT)
        self.assertIsNone(approval_request.current_step)
        self.assertIsNone(approval_request.submitted_at)

    def test_create_allows_same_user_as_both_approvers(self):
        response = self.client.post(
            REQUESTS_URL,
            self.payload(
                first_approver_id=self.first.pk,
                second_approver_id=self.first.pk,
            ),
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        approval_request = ApprovalRequest.objects.get(pk=response.data["id"])
        self.assertEqual(approval_request.first_approver, self.first)
        self.assertEqual(approval_request.second_approver, self.first)

    def test_create_rejects_applicant_as_approver(self):
        for field in ("first_approver_id", "second_approver_id"):
            with self.subTest(field=field):
                payload = self.payload(**{field: self.applicant.pk})
                response = self.client.post(REQUESTS_URL, payload, format="json")

                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.data["code"], "validation_error")
                self.assertIn(field, response.data["details"])

    def test_create_rejects_unknown_approver(self):
        response = self.client.post(
            REQUESTS_URL,
            self.payload(first_approver_id=999999),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("first_approver_id", response.data["details"])

    def test_create_validates_required_and_whitespace_fields(self):
        cases = (
            ("title", "   "),
            ("content", "\n\t "),
        )
        for field, value in cases:
            with self.subTest(field=field):
                response = self.client.post(
                    REQUESTS_URL,
                    self.payload(**{field: value}),
                    format="json",
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data["details"])

    def test_create_validates_field_lengths(self):
        cases = (
            ("title", "t" * 101),
            ("content", "c" * 2001),
        )
        for field, value in cases:
            with self.subTest(field=field):
                response = self.client.post(
                    REQUESTS_URL,
                    self.payload(**{field: value}),
                    format="json",
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data["details"])

    def test_create_requires_all_fields(self):
        response = self.client.post(REQUESTS_URL, {}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            set(response.data["details"]),
            {
                "title",
                "content",
                "first_approver_id",
                "second_approver_id",
            },
        )


class ListDraftTests(DraftApiTestCase):
    def test_list_returns_only_current_user_requests(self):
        own = self.create_request(title="我发起的")
        self.create_request(applicant=self.outsider, title="别人的申请")

        response = self.client.get(REQUESTS_URL)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual([item["id"] for item in response.data["results"]], [own.pk])
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["page_size"], 10)

    def test_list_filters_and_paginates_after_filtering(self):
        for index in range(12):
            status = (
                ApprovalRequest.Status.DRAFT
                if index % 2 == 0
                else ApprovalRequest.Status.IN_REVIEW
            )
            self.create_request(
                title=f"采购显示器 {index}",
                status=status,
                current_step=1 if status == ApprovalRequest.Status.IN_REVIEW else None,
            )
        self.create_request(
            applicant=self.outsider,
            title="别人的采购",
        )

        response = self.client.get(
            REQUESTS_URL,
            {
                "page": 2,
                "pageSize": 5,
                "status": "draft",
                "keyword": "采购显示器",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 6)
        self.assertEqual(response.data["page"], 2)
        self.assertEqual(response.data["page_size"], 5)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertTrue(
            all(item["status"] == "draft" for item in response.data["results"])
        )

    def test_list_orders_by_created_at_and_id_descending(self):
        older = self.create_request(title="较早申请")
        newer = self.create_request(title="较新申请")
        fixed_time = timezone.now() - timedelta(days=1)
        ApprovalRequest.objects.filter(pk__in=[older.pk, newer.pk]).update(
            created_at=fixed_time
        )

        response = self.client.get(REQUESTS_URL)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["results"]],
            [newer.pk, older.pk],
        )

    def test_list_rejects_pending_scope(self):
        response = self.client.get(REQUESTS_URL, {"scope": "pending"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "scope_not_available")
        self.assertIn("尚未开放", response.data["message"])

    def test_list_rejects_invalid_pagination(self):
        for params in ({"page": 0}, {"pageSize": 0}, {"pageSize": 101}):
            with self.subTest(params=params):
                response = self.client.get(REQUESTS_URL, params)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.data["code"], "validation_error")


class DetailDraftTests(DraftApiTestCase):
    def test_detail_allows_applicant_and_approvers_with_empty_history(self):
        approval_request = self.create_request()

        for user in (self.applicant, self.first, self.second):
            with self.subTest(user=user.username):
                self.client.force_authenticate(user=user)
                response = self.client.get(self.request_detail_url(approval_request.pk))

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["id"], approval_request.pk)
                self.assertEqual(response.data["history"], [])
                self.assertEqual(response.data["status"], "draft")

    def test_detail_rejects_unrelated_user(self):
        approval_request = self.create_request()
        self.client.force_authenticate(user=self.outsider)

        response = self.client.get(self.request_detail_url(approval_request.pk))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "forbidden")

    def test_detail_returns_404_for_missing_request(self):
        response = self.client.get(self.request_detail_url(999999))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], "not_found")

    def test_detail_computes_current_approver_from_status_and_step(self):
        first_step = self.create_request(
            status=ApprovalRequest.Status.IN_REVIEW,
            current_step=1,
            submitted_at=timezone.now(),
        )
        second_step = self.create_request(
            title="二级申请",
            status=ApprovalRequest.Status.IN_REVIEW,
            current_step=2,
            submitted_at=timezone.now(),
        )

        first_response = self.client.get(self.request_detail_url(first_step.pk))
        second_response = self.client.get(self.request_detail_url(second_step.pk))

        self.assertEqual(first_response.data["current_approver"]["id"], self.first.pk)
        self.assertEqual(second_response.data["current_approver"]["id"], self.second.pk)


class UpdateDraftTests(DraftApiTestCase):
    def test_applicant_can_update_draft(self):
        approval_request = self.create_request()
        original_updated_at = approval_request.updated_at

        response = self.client.put(
            self.request_detail_url(approval_request.pk),
            self.payload(
                title="更新后的标题",
                content="更新后的内容",
                first_approver_id=self.second.pk,
                second_approver_id=self.first.pk,
            ),
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "更新后的标题")
        self.assertEqual(response.data["content"], "更新后的内容")
        self.assertEqual(response.data["first_approver"]["id"], self.second.pk)
        self.assertEqual(response.data["second_approver"]["id"], self.first.pk)

        approval_request.refresh_from_db()
        self.assertGreater(approval_request.updated_at, original_updated_at)
        self.assertEqual(approval_request.status, ApprovalRequest.Status.DRAFT)

    def test_update_requires_all_four_fields(self):
        approval_request = self.create_request()

        response = self.client.put(
            self.request_detail_url(approval_request.pk),
            {"title": "只改标题"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            set(response.data["details"]),
            {"content", "first_approver_id", "second_approver_id"},
        )

    def test_approver_cannot_update_or_delete(self):
        approval_request = self.create_request()
        self.client.force_authenticate(user=self.first)

        update = self.client.put(
            self.request_detail_url(approval_request.pk),
            self.payload(),
            format="json",
        )
        delete = self.client.delete(self.request_detail_url(approval_request.pk))

        self.assertEqual(update.status_code, 403)
        self.assertEqual(delete.status_code, 403)

    def test_applicant_cannot_update_non_draft(self):
        approval_request = self.create_request(
            status=ApprovalRequest.Status.IN_REVIEW,
            current_step=1,
            submitted_at=timezone.now(),
        )

        response = self.client.put(
            self.request_detail_url(approval_request.pk),
            self.payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "conflict")


class DeleteDraftTests(DraftApiTestCase):
    def test_applicant_can_delete_draft(self):
        approval_request = self.create_request()

        response = self.client.delete(self.request_detail_url(approval_request.pk))

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(
            ApprovalRequest.objects.filter(pk=approval_request.pk).exists()
        )

    def test_approver_cannot_delete_draft(self):
        approval_request = self.create_request()
        self.client.force_authenticate(user=self.second)

        response = self.client.delete(self.request_detail_url(approval_request.pk))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            ApprovalRequest.objects.filter(pk=approval_request.pk).exists()
        )

    def test_applicant_cannot_delete_non_draft(self):
        approval_request = self.create_request(
            status=ApprovalRequest.Status.APPROVED,
            submitted_at=timezone.now(),
        )

        response = self.client.delete(self.request_detail_url(approval_request.pk))

        self.assertEqual(response.status_code, 409)
        self.assertTrue(
            ApprovalRequest.objects.filter(pk=approval_request.pk).exists()
        )


class AuthenticationAndUserListTests(DraftApiTestCase):
    def test_requests_require_authentication(self):
        client = APIClient()

        list_response = client.get(REQUESTS_URL)
        create_response = client.post(REQUESTS_URL, self.payload(), format="json")

        self.assertEqual(list_response.status_code, 401)
        self.assertEqual(create_response.status_code, 401)

    def test_users_list_returns_summaries_for_authenticated_user(self):
        response = self.client.get("/api/users")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 4)
        self.assertEqual(
            set(response.data[0]),
            {"id", "username", "display_name"},
        )
        usernames = {item["username"] for item in response.data}
        self.assertEqual(
            usernames,
            {"applicant", "first", "second", "outsider"},
        )
