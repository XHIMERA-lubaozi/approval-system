"""申请单草稿接口。"""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from approvals.exceptions import ScopeNotAvailable
from approvals.models import ApprovalRequest
from approvals.serializers import (
    ApprovalRequestDetailSerializer,
    ApprovalRequestSerializer,
    DraftInputSerializer,
    RequestListQuerySerializer,
)
from approvals.services import ensure_can_modify_draft, ensure_can_view


def _request_queryset():
    return ApprovalRequest.objects.select_related(
        "applicant",
        "first_approver",
        "second_approver",
    )


def _get_request_or_404(pk):
    return get_object_or_404(_request_queryset(), pk=pk)


class RequestListCreateView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query = RequestListQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data

        if params["scope"] != "mine":
            raise ScopeNotAvailable()

        requests = _request_queryset().filter(applicant=request.user)

        status_filter = params.get("status")
        if status_filter:
            requests = requests.filter(status=status_filter)

        keyword = params.get("keyword", "").strip()
        if keyword:
            requests = requests.filter(title__icontains=keyword)

        requests = requests.order_by("-created_at", "-id")
        count = requests.count()
        page = params["page"]
        page_size = params["pageSize"]
        start = (page - 1) * page_size
        page_items = requests[start : start + page_size]

        return Response(
            {
                "count": count,
                "page": page,
                "page_size": page_size,
                "results": ApprovalRequestSerializer(page_items, many=True).data,
            }
        )

    def post(self, request):
        serializer = DraftInputSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        approval_request = serializer.save()
        return Response(
            ApprovalRequestSerializer(approval_request).data,
            status=status.HTTP_201_CREATED,
        )


class RequestDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        approval_request = _get_request_or_404(pk)
        ensure_can_view(approval_request, request.user)
        return Response(
            ApprovalRequestDetailSerializer(approval_request).data,
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        approval_request = _get_request_or_404(pk)
        ensure_can_modify_draft(approval_request, request.user)

        serializer = DraftInputSerializer(
            instance=approval_request,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        approval_request = serializer.save()
        return Response(
            ApprovalRequestSerializer(approval_request).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        approval_request = _get_request_or_404(pk)
        ensure_can_modify_draft(approval_request, request.user)
        approval_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
