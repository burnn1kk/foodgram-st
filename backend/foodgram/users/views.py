from rest_framework import status
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from djoser.views import TokenCreateView

from django.contrib.auth.password_validation import validate_password
from .models import User
from .serializers import (
    CustomUserSerializer,
    SetPasswordSerializer,
    CustomTokenCreateSerializer
)

class CustomTokenCreateView(TokenCreateView):
    serializer_class = CustomTokenCreateSerializer


class UserViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)