from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .serializers import (UserSerializer, ChangePasswordSerializer,
                          TagSerializer, IngredientSerializer,
                          ReceiptGetSerializer, ReceiptCreateSerializer)
from rest_framework.decorators import action
from .models import User, Tag, Ingredient, Receipt
from rest_framework.pagination import PageNumberPagination


class UserViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def list(self, request):
        users = User.objects.all()
        paginator = PageNumberPagination()
        paginator.page_size = 6
        page = paginator.paginate_queryset(users, request)
        serializer = UserSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request, pk=None):
        if pk == 'me':
            user = request.user
            serializer = UserSerializer(user)
            return Response(serializer.data)
        user = User.objects.get(id=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='set_password')
    def set_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            current_password = serializer.validated_data['current_password']
            if not user.check_password(current_password):
                return Response({"error": "Invalid current password"},
                                status=400)

            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            user.save()
            return Response(status=204)
        else:
            return Response(serializer.errors, status=400)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class ReceiptViewSet(viewsets.ModelViewSet):
    queryset = Receipt.objects.all()
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ReceiptGetSerializer
        return ReceiptCreateSerializer
