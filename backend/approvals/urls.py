from django.urls import path

from approvals.views import RequestDetailView, RequestListCreateView, SubmitView, ApproveView, RejectView, HistoryView


urlpatterns = [
    path("requests", RequestListCreateView.as_view(), name="request-list-create"),
    path("requests/<int:pk>/submit", SubmitView.as_view()),
    path("requests/<int:pk>/reject", RejectView.as_view()),
    path("requests/<int:pk>/history", HistoryView.as_view()),
    path("requests/<int:pk>/approve", ApproveView.as_view()),
    path("requests/<int:pk>", RequestDetailView.as_view(), name="request-detail"),
]
