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
