from django.db.models import Prefetch
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .filters import ReceiptFilter
from .models import (Favorite, Ingredient, Receipt, ShoppingCart, Subscribe,
                     Tag, User)
from .serializers import (ChangePasswordSerializer, IngredientSerializer,
                          ReceiptCreateSerializer, ReceiptGetSerializer,
                          TagSerializer, UserSerializer,
                          UserSubscriptionSerializer)


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

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def subscriptions(self, request):
        user = request.user
        subscribed_authors = User.objects.filter(
            creator__user=user).prefetch_related(
                Prefetch('recipes', queryset=Receipt.objects.all()))

        paginator = PageNumberPagination()
        paginator.page_size = 6

        page = paginator.paginate_queryset(subscribed_authors, request)
        if page is not None:
            serializer = UserSubscriptionSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = UserSubscriptionSerializer(subscribed_authors, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        author = User.objects.get(id=pk)
        if request.method == 'POST':
            Subscribe.objects.get_or_create(user=request.user,
                                            author=author)
            return Response(status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            Subscribe.objects.filter(user=request.user,
                                     author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


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
    queryset = Receipt.objects.all().order_by('-id')
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = ReceiptFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ReceiptGetSerializer
        return ReceiptCreateSerializer

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            Favorite.objects.get_or_create(user=request.user, recipe=recipe)
            return Response(status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            Favorite.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            ShoppingCart.objects.get_or_create(user=request.user,
                                               recipe=recipe)
            return Response(status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            ShoppingCart.objects.filter(user=request.user,
                                        recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        cart_items = ShoppingCart.objects.filter(user=request.user)
        recipes = Receipt.objects.filter(
            id__in=cart_items.values_list('recipe', flat=True))

        ingredients = {}

        for recipe in recipes:
            recipe_ingredients = ReceiptGetSerializer().get_ingredients(recipe)
            for ingredient in recipe_ingredients:
                name = ingredient['name']
                amount = ingredient['amount']
                measurement_unit = ingredient['measurement_unit']
                if name in ingredients:
                    ingredients[name]['amount'] += amount
                else:
                    ingredients[name] = {
                        'amount': amount,
                        'measurement_unit': measurement_unit}
        file_content = ''
        for name, details in ingredients.items():
            file_content += f"{name}: {details['amount']} \
                {details['measurement_unit']}\n"

        return HttpResponse(file_content, content_type='text/plain')
