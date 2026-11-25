from django.http import HttpResponse
from django.urls import include, path


def health_check(request):
    return HttpResponse(status=204)


urlpatterns = [
    path("healthz", health_check),
    path("api/", include("users.urls")),
    path("api/", include("approvals.urls")),
]
