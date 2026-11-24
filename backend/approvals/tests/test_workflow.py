"""审批流程接口测试：提交、两级通过、驳回、历史写入回滚与步骤重放。"""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from approvals.models import ApprovalRequest, OperationHistory
from approvals.services import transition
from approvals.tests.test_drafts import DraftApiTestCase


class WorkflowTests(DraftApiTestCase):
    def test_submit_and_two_approvals(self):
        obj = self.create_request()
        url = self.request_detail_url(obj.pk)
        self.assertEqual(self.client.post(url + '/submit').status_code, 200)
        self.client.force_authenticate(user=self.second)
        self.assertEqual(self.client.post(url + '/approve', {'expected_step': 2}, format='json').status_code, 403)
        self.client.force_authenticate(user=self.first)
        response = self.client.post(url + '/approve', {'expected_step': 1}, format='json')
        self.assertEqual((response.status_code, response.data['current_step']), (200, 2))
        self.client.force_authenticate(user=self.second)
        self.assertEqual(self.client.post(url + '/approve', {'expected_step': 2}, format='json').data['status'], 'approved')
        self.assertEqual(self.client.post(url + '/approve', {'expected_step': 2}, format='json').status_code, 409)
        self.assertEqual(len(self.client.get(url).data['history']), 3)

    def test_reject_and_pending_and_history_permissions(self):
        obj = self.create_request()
        url = self.request_detail_url(obj.pk)
        self.client.post(url + '/submit')
        self.client.force_authenticate(user=self.first)
        self.assertEqual(self.client.get('/api/requests?scope=pending').data['count'], 1)
        self.assertEqual(self.client.post(url + '/reject', {'expected_step': 1, 'comment': '  '}, format='json').status_code, 400)
        result = self.client.post(url + '/reject', {'expected_step': 1, 'comment': '  退回  '}, format='json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['status'], 'rejected')
        self.assertEqual(self.client.get('/api/requests?scope=pending').data['count'], 0)
        self.assertEqual(self.client.get(url + '/history').data[-1]['comment'], '退回')
        self.client.force_authenticate(user=self.outsider)
        self.assertEqual(self.client.get(url + '/history').status_code, 403)

    def test_second_step_reject_and_invalid_comment(self):
        obj = self.create_request()
        url = self.request_detail_url(obj.pk)
        self.client.post(url + '/submit')
        self.client.force_authenticate(user=self.first)
        self.client.post(url + '/approve', {'expected_step': 1}, format='json')
        self.assertEqual(self.client.post(url + '/reject', {'expected_step': 2, 'comment': 'x'}, format='json').status_code, 403)
        self.client.force_authenticate(user=self.second)
        self.assertEqual(self.client.post(url + '/reject', {'expected_step': 2, 'comment': 'x' * 501}, format='json').status_code, 400)
        result = self.client.post(url + '/reject', {'expected_step': 2, 'comment': '不同意'}, format='json')
        self.assertEqual(result.data['status'], 'rejected')
        self.assertIsNone(result.data['current_step'])
        self.assertEqual([h['action'] for h in self.client.get(url + '/history').data], ['submit', 'approve', 'reject'])


class ReplayApprovalTests(DraftApiTestCase):
    """同一用户担任两级审批人时，旧步骤请求不得推进流程。"""

    def test_stale_step_replay_rejected_then_next_step_completes(self):
        approver = self.first
        obj = self.create_request(first=approver, second=approver)
        url = self.request_detail_url(obj.pk)

        self.assertEqual(self.client.post(url + '/submit').status_code, 200)
        self.client.force_authenticate(user=approver)

        first = self.client.post(url + '/approve', {'expected_step': 1}, format='json')
        self.assertEqual(first.status_code, 200)
        self.assertEqual((first.data['status'], first.data['current_step']), ('in_review', 2))
        history_after_first = self.client.get(url + '/history').data
        self.assertEqual([item['action'] for item in history_after_first], ['submit', 'approve'])

        replay = self.client.post(url + '/approve', {'expected_step': 1}, format='json')
        self.assertEqual(replay.status_code, 409)
        self.assertEqual(replay.data['code'], 'conflict')

        stored = ApprovalRequest.objects.get(pk=obj.pk)
        self.assertEqual((stored.status, stored.current_step), (ApprovalRequest.Status.IN_REVIEW, 2))
        self.assertEqual(stored.current_approver.pk, approver.pk)
        self.assertEqual(
            OperationHistory.objects.filter(request=obj).count(),
            len(history_after_first),
        )

        detail = self.client.get(url)
        self.assertEqual(detail.data['status'], 'in_review')
        self.assertEqual(detail.data['current_step'], 2)
        self.assertEqual(detail.data['current_approver']['id'], approver.pk)
        self.assertEqual(detail.data['history'], history_after_first)

        second = self.client.post(url + '/approve', {'expected_step': 2}, format='json')
        self.assertEqual(second.status_code, 200)
        self.assertEqual((second.data['status'], second.data['current_step']), ('approved', None))
        self.assertIsNone(second.data['current_approver'])
        self.assertEqual(
            [item['action'] for item in self.client.get(url + '/history').data],
            ['submit', 'approve', 'approve'],
        )
        self.assertEqual(
            OperationHistory.objects.filter(request=obj).count(),
            len(history_after_first) + 1,
        )


class TransactionWorkflowTests(TransactionTestCase):
    def setUp(self):
        User = get_user_model()
        self.applicant = User.objects.create_user(username='tx_applicant', password='Pass123!')
        self.approver = User.objects.create_user(username='tx_approver', password='Pass123!')
        self.obj = self.create_request()
        transition(self.obj.pk, self.applicant, 'submit')

    def create_request(self):
        return ApprovalRequest.objects.create(
            title='测试',
            content='内容',
            applicant=self.applicant,
            first_approver=self.approver,
            second_approver=self.approver,
        )

    def read_history(self, obj):
        """读取历史快照，用于对比“保持不变”与“没有新增”。"""
        return list(
            OperationHistory.objects.filter(request=obj)
            .order_by('id')
            .values(
                'id',
                'operator_id',
                'action',
                'step',
                'comment',
                'before_status',
                'before_step',
                'after_status',
                'after_step',
                'operated_at',
            )
        )

    def assert_history_failure_rolls_back(
        self,
        action,
        user,
        expected_step=None,
        comment=None,
        target=None,
        attempted_state=None,
    ):
        """仅让历史写入失败，断言申请单在事务回滚后保持操作前的全部字段。"""
        target = target or self.obj
        before = ApprovalRequest.objects.get(pk=target.pk)
        before_history = self.read_history(target)
        attempted = {}

        def fail_create(**kwargs):
            # 与业务代码共用同一事务连接：此处能读到已更新的申请单，说明状态已尝试写入，
            # 失败只发生在紧随其后的历史写入。
            in_transaction = ApprovalRequest.objects.get(pk=target.pk)
            attempted['status'] = in_transaction.status
            attempted['current_step'] = in_transaction.current_step
            attempted['submitted_at'] = in_transaction.submitted_at
            raise RuntimeError('write failed')

        with patch.object(OperationHistory.objects, 'create', side_effect=fail_create):
            with self.assertRaises(RuntimeError):
                transition(target.pk, user, action, expected_step, comment)

        self.assertEqual(
            (attempted['status'], attempted['current_step']),
            attempted_state,
        )
        if action == 'submit':
            # 提交前 submitted_at 为空；事务内已被写入，说明状态更新确实执行过。
            self.assertIsNone(before.submitted_at)
            self.assertIsNotNone(attempted['submitted_at'])

        after = ApprovalRequest.objects.get(pk=target.pk)
        self.assertEqual(after.status, before.status)
        self.assertEqual(after.current_step, before.current_step)
        self.assertEqual(after.submitted_at, before.submitted_at)
        self.assertEqual(after.updated_at, before.updated_at)
        self.assertEqual(self.read_history(target), before_history)
        self.assertEqual(
            OperationHistory.objects.filter(request=target).count(),
            len(before_history),
        )
        return before, after

    def test_history_failure_rolls_back_submit(self):
        draft = self.create_request()
        self.assert_history_failure_rolls_back(
            'submit',
            self.applicant,
            target=draft,
            attempted_state=(ApprovalRequest.Status.IN_REVIEW, 1),
        )

    def test_history_failure_rolls_back_first_approval(self):
        self.assert_history_failure_rolls_back(
            'approve',
            self.approver,
            1,
            target=self.obj,
            attempted_state=(ApprovalRequest.Status.IN_REVIEW, 2),
        )

    def test_history_failure_rolls_back_second_approval(self):
        transition(self.obj.pk, self.approver, 'approve', 1)
        self.assert_history_failure_rolls_back(
            'approve',
            self.approver,
            2,
            target=self.obj,
            attempted_state=(ApprovalRequest.Status.APPROVED, None),
        )

    def test_history_failure_rolls_back_rejection(self):
        self.assert_history_failure_rolls_back(
            'reject',
            self.approver,
            1,
            '理由',
            target=self.obj,
            attempted_state=(ApprovalRequest.Status.REJECTED, None),
        )

    def test_history_failure_surfaces_500_and_keeps_draft_unsubmitted(self):
        draft = self.create_request()
        before = ApprovalRequest.objects.get(pk=draft.pk)
        client = APIClient()
        client.force_authenticate(user=self.applicant)

        with patch.object(OperationHistory.objects, 'create', side_effect=RuntimeError('write failed')):
            with self.assertLogs('common.exceptions', level='ERROR') as captured:
                response = client.post(f'/api/requests/{draft.pk}/submit')

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['code'], 'internal_error')
        self.assertIn('RuntimeError', '\n'.join(captured.output))

        after = ApprovalRequest.objects.get(pk=draft.pk)
        self.assertEqual(
            (after.status, after.current_step, after.submitted_at, after.updated_at),
            (before.status, before.current_step, before.submitted_at, before.updated_at),
        )
        self.assertFalse(OperationHistory.objects.filter(request=draft).exists())

    def test_approve_reject_compete_on_independent_connections(self):
        self.assertEqual(connection.vendor, 'postgresql')
        barrier = Barrier(2)
        def run(action):
            close_old_connections()
            user = get_user_model().objects.get(pk=self.approver.pk)
            barrier.wait(timeout=10)
            try:
                transition(self.obj.pk, user, action, 1, '理由')
                return 'ok'
            except Exception as exc:
                return getattr(exc, 'status_code', None)
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, ['approve', 'reject']))
        self.assertCountEqual(results, ['ok', 409])
        self.assertEqual(OperationHistory.objects.filter(request=self.obj).count(), 2)
