"""注册、登录、当前用户与审批人候选接口。"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from users.serializers import LoginSerializer, RegisterSerializer, UserSerializer


User = get_user_model()


class RegisterView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token = AccessToken.for_user(user)
        return Response(
            {"access_token": str(token), "token_type": "Bearer"},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


class UserListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        users = User.objects.order_by("id")
        return Response(
            UserSerializer(users, many=True).data,
            status=status.HTTP_200_OK,
        )
