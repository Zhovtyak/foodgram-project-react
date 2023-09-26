from django.db.models import Prefetch
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .filters import ReceiptFilter, IngredientFilter
from recipes.models import (Favorite, Ingredient, Receipt, ShoppingCart, Tag)
from users.models import User, Subscribe
from .serializers import (ChangePasswordSerializer, IngredientSerializer,
                          ReceiptCreateSerializer, ReceiptGetSerializer,
                          TagSerializer, UserSerializer,
                          UserSubscriptionSerializer, SubscribeSerializer,
                          FavoriteSerializer, ShoppingCartSerializer)
from .utils import forming_shopping_cart_file
from .permissions import IsOwnerOrReadOnly


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSerializer
    queryset = User.objects.all()
    pagination_class = PageNumberPagination

    def create(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        if pk == 'me':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        user = get_object_or_404(User, id=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='set_password',
            permission_classes=[permissions.IsAuthenticated])
    def set_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            current_password = serializer.validated_data['current_password']
            if not user.check_password(current_password):
                return Response({'error': 'Invalid current password'},
                                status=400)
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            user.save()
            return Response(status=204)

    @action(detail=False, methods=['get'], url_path='subscriptions',
            permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        subscribed_authors = User.objects.filter(
            creator__user=request.user).prefetch_related(
                Prefetch('recipes', queryset=Receipt.objects.all()))

        paginator = PageNumberPagination()
        paginator.page_size = 6

        page = paginator.paginate_queryset(subscribed_authors, request)
        serializer = UserSubscriptionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, id=pk)
        serializer = SubscribeSerializer(data={'user': request.user.pk,
                                               'author': author.pk})
        if request.method == 'POST':
            if serializer.is_valid():
                serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            subscribe = get_object_or_404(Subscribe, user=request.user,
                                          author=author)
            subscribe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class ReceiptViewSet(viewsets.ModelViewSet):
    queryset = Receipt.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = ReceiptFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ReceiptGetSerializer
        return ReceiptCreateSerializer

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            serializer = FavoriteSerializer(data={'user': request.user.id,
                                                  'recipe': recipe.id})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            instance = get_object_or_404(Favorite, user=request.user,
                                         recipe=recipe)
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(data={'user': request.user.id,
                                                      'recipe': recipe.id})
            if serializer.is_valid():
                serializer.save()
                return Response(
                                status=status.HTTP_201_CREATED)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            instance = get_object_or_404(ShoppingCart, user=request.user,
                                         recipe=recipe)
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        cart_items = ShoppingCart.objects.filter(user=request.user)
        recipes = Receipt.objects.filter(
            id__in=cart_items.values_list(
                'recipe', flat=True)).prefetch_related('receipt_ingredient')
        return HttpResponse(forming_shopping_cart_file(recipes),
                            content_type='text/plain')
