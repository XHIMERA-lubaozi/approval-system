from django.urls import path

from approvals.views import RequestDetailView, RequestListCreateView


urlpatterns = [
    path("requests", RequestListCreateView.as_view(), name="request-list-create"),
    path("requests/<int:pk>", RequestDetailView.as_view(), name="request-detail"),
]
