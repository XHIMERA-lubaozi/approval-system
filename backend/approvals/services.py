"""申请单权限判断。"""

from rest_framework.exceptions import PermissionDenied

from approvals.exceptions import DraftNotEditable
from approvals.models import ApprovalRequest


def ensure_can_view(approval_request, user):
    allowed_user_ids = {
        approval_request.applicant_id,
        approval_request.first_approver_id,
        approval_request.second_approver_id,
    }
    if user.id not in allowed_user_ids:
        raise PermissionDenied("无权查看该申请")


def ensure_can_modify_draft(approval_request, user):
    if approval_request.applicant_id != user.id:
        raise PermissionDenied("只有申请人可以修改该申请")
    if approval_request.status != ApprovalRequest.Status.DRAFT:
        raise DraftNotEditable()


from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from approvals.models import OperationHistory


@transaction.atomic
def transition(pk, user, action, expected_step=None, comment=None):
    obj = get_object_or_404(ApprovalRequest.objects.select_for_update(), pk=pk)
    before_status, before_step = obj.status, obj.current_step
    if action == 'submit':
        if obj.applicant_id != user.id:
            raise PermissionDenied('只有申请人可以提交')
        if obj.status != ApprovalRequest.Status.DRAFT:
            raise DraftNotEditable()
        obj.status = ApprovalRequest.Status.IN_REVIEW
        obj.current_step = 1
        obj.submitted_at = timezone.now()
        step = None
    else:
        if obj.status != ApprovalRequest.Status.IN_REVIEW:
            raise DraftNotEditable()
        # A stale request by a participant is a conflict; an unrelated user is forbidden.
        if user.id not in (obj.first_approver_id, obj.second_approver_id):
            raise PermissionDenied('无权审批该申请')
        if expected_step != obj.current_step:
            if user.id == (obj.first_approver_id if expected_step == 1 else obj.second_approver_id) and expected_step < obj.current_step:
                raise DraftNotEditable()
            raise PermissionDenied('尚未轮到您审批')
        if obj.current_approver.id != user.id:
            raise PermissionDenied('无权审批该申请')
        step = obj.current_step
        if action == "reject":
            obj.current_step = None
            obj.status = ApprovalRequest.Status.REJECTED
        elif step == 1:
            obj.current_step = 2
        else:
            obj.current_step = None
            obj.status = ApprovalRequest.Status.APPROVED
    obj.save()
    OperationHistory.objects.create(request=obj, operator=user, action=action, step=step,
        comment=comment if action in ('approve', 'reject') else None, before_status=before_status,
        before_step=before_step, after_status=obj.status, after_step=obj.current_step)
    return obj
