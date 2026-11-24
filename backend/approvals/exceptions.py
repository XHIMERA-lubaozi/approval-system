"""申请单相关的业务异常。"""

from rest_framework import status
from rest_framework.exceptions import APIException


class ScopeNotAvailable(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "待我审批视图尚未开放"
    default_code = "scope_not_available"


class DraftNotEditable(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "只有草稿可以编辑或删除"
    default_code = "conflict"
