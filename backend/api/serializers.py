import base64

from api.models import (Favorite, Ingredient, Receipt, ReceiptIngredient,
                        ShoppingCart, Subscribe, Tag, User)
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.fields import DictField, ListField


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username',
                  'first_name', 'last_name', 'password', 'is_subscribed']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscribe.objects.filter(user=request.user,
                                            author=obj).exists()
        return False


class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=128)
    current_password = serializers.CharField(max_length=128)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class ReceiptIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = ReceiptIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class ReceiptGetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Receipt
        fields = ['id', 'name', 'ingredients', 'tags',
                  'image', 'text', 'cooking_time', 'author',
                  'is_favorited', 'is_in_shopping_cart']

    def get_ingredients(self, obj):
        qs = obj.receiptingredient_set.all()
        return ReceiptIngredientSerializer(qs, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user, recipe=obj).exists()
        return False


class Base64EncodedImageField(serializers.ImageField):
    def to_internal_value(self, data):
        format, imgstr = data.split(';base64,')
        ext = format.split('/')[-1]
        return ContentFile(base64.b64decode(imgstr), name='temp.' + ext)


class ReceiptCreateSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = ListField(child=DictField(),
                            write_only=True)
    image = Base64EncodedImageField()

    class Meta:
        model = Receipt
        fields = ['id', 'name', 'ingredients', 'tags',
                  'image', 'text', 'cooking_time', 'author']

    def validate_ingredients(self, ingredients):
        for ingredient in ingredients:
            if not all(key in ingredient for key in ('id', 'amount')):
                raise serializers.ValidationError(
                    "Ингредиент должен иметь 'id' и 'amount'")
        return ingredients

    def create_ingredients(self, ingredients, receipt):
        ingredients_list = [
            ReceiptIngredient(
                receipt=receipt,
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ]
        ReceiptIngredient.objects.bulk_create(ingredients_list)

    def create(self, validated_data):
        author = self.context.get('request').user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        receipt = Receipt.objects.create(author=author, **validated_data)
        self.create_ingredients(ingredients, receipt)
        receipt.tags.set(tags)
        return receipt

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        self.create_ingredients(
            validated_data.pop('ingredients'), instance
        )
        return super().update(instance, validated_data)


class UserSubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = ReceiptGetSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count']

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscribe.objects.filter(user=request.user,
                                            author=obj).exists()
        return False

    def get_recipes_count(self, obj):
        return obj.recipes.count()
