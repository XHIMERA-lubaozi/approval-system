from django.urls import path

from users.views import LoginView, MeView, RegisterView, UserListView


urlpatterns = [
    path("auth/register", RegisterView.as_view(), name="auth-register"),
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("users/me", MeView.as_view(), name="users-me"),
    path("users", UserListView.as_view(), name="users-list"),
]
