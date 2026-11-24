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


from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from approvals.models import ApprovalRequest, OperationHistory
from approvals.services import transition


class TransactionWorkflowTests(TransactionTestCase):
    def setUp(self):
        User = get_user_model()
        self.applicant = User.objects.create_user(username='tx_applicant', password='Pass123!')
        self.approver = User.objects.create_user(username='tx_approver', password='Pass123!')
        self.obj = ApprovalRequest.objects.create(title='测试', content='内容', applicant=self.applicant,
            first_approver=self.approver, second_approver=self.approver)
        transition(self.obj.pk, self.applicant, 'submit')

    def test_history_failure_rolls_back_rejection(self):
        before = ApprovalRequest.objects.get(pk=self.obj.pk)
        with patch.object(OperationHistory.objects, 'create', side_effect=RuntimeError('write failed')):
            with self.assertRaises(RuntimeError):
                transition(self.obj.pk, self.approver, 'reject', 1, '理由')
        after = ApprovalRequest.objects.get(pk=self.obj.pk)
        self.assertEqual((after.status, after.current_step, after.updated_at, after.submitted_at),
                         (before.status, before.current_step, before.updated_at, before.submitted_at))
        self.assertEqual(after.history.count(), 1)

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
