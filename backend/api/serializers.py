import base64

from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import check_password
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, Receipt, ReceiptIngredient,
                            ShoppingCart, Tag)
from users.models import User, Subscribe
from .constants import MAX_PASSWORD_LENGTH
from recipes.constants import (MAX_COOKING_TIME, MIN_COOKING_TIME,
                               MIN_AMOUNT, MAX_AMOUNT)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed']

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and request.user.subscriber.filter(author=obj).exists())


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=MAX_PASSWORD_LENGTH)
    current_password = serializers.CharField(max_length=MAX_PASSWORD_LENGTH)

    def validate(self, data):
        user = self.context['request'].user
        if not check_password(data['current_password'], user.password):
            raise serializers.ValidationError('Неверный текущий пароль')
        return data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngredientSerializer(serializers.ModelSerializer):
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
    ingredients = RecipeIngredientSerializer(
        source='receipt_ingredient', many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Receipt
        fields = ['id', 'name', 'ingredients', 'tags',
                  'image', 'text', 'cooking_time', 'author',
                  'is_favorited', 'is_in_shopping_cart']

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and request.user.favorites.filter(recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and request.user.shopping_carts.filter(recipe=obj).exists())


class Base64EncodedImageField(serializers.ImageField):
    def to_internal_value(self, data):
        format, imgstr = data.split(';base64,')
        ext = format.split('/')[-1]
        return ContentFile(base64.b64decode(imgstr), name='temp.' + ext)


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ReceiptIngredient
        fields = ['id', 'amount']

    def validate_id(self, id):
        if not Ingredient.objects.filter(id=id).exists():
            raise serializers.ValidationError(
                'Такого ингредиента не существует!')
        return id


class ReceiptCreateSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64EncodedImageField()

    class Meta:
        model = Receipt
        fields = ['id', 'name', 'ingredients', 'tags',
                  'image', 'text', 'cooking_time', 'author']

    def validate_cooking_time(self, cooking_time):
        if (cooking_time > MAX_COOKING_TIME
                or cooking_time < MIN_COOKING_TIME):
            raise serializers.ValidationError(
                'Время приготовления должно быть в диапазоне 1-10000')
        return cooking_time

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Должен быть выбран минимум один ингредиент')
        ingredient_ids = set()
        for ingredient in ingredients:
            if not all(key in ingredient for key in ('id', 'amount')):
                raise serializers.ValidationError(
                    'Ингредиент должен содержать id и amount')
            ingredient_id = ingredient['id']
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться')
            ingredient_ids.add(ingredient_id)
            get_object_or_404(Ingredient, id=ingredient_id)
            amount = ingredient['amount']
            if not isinstance(amount, int):
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть целым числом')
            if amount < MIN_AMOUNT or amount > MAX_AMOUNT:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть в диапазоне 1-10000')
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Должен быть выбран минимум один тэг')
        tag_ids = set()
        for tag in tags:
            if tag.id in tag_ids:
                raise serializers.ValidationError(
                    'Тэги не должны повторяться')
            tag_ids.add(tag.id)
            get_object_or_404(Tag, id=tag.id)
        return tags

    def create_ingredients(self, ingredients, receipt):
        ingredients_list = [
            ReceiptIngredient(
                recipe=receipt,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        ReceiptIngredient.objects.bulk_create(ingredients_list)

    def create(self, validated_data):
        author = self.context.get('request').user
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        receipt = Receipt.objects.create(author=author, **validated_data)
        self.create_ingredients(ingredients_data, receipt)
        receipt.tags.set(tags)
        return receipt

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        self.create_ingredients(
            validated_data.pop('ingredients'), instance
        )
        instance.tags.set(
            validated_data.pop('tags'))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return ReceiptGetSerializer(instance, context=self.context).data


class ReceiptRepresantaionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ['id', 'name', 'image', 'cooking_time']


class UserSubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['recipes', 'recipes_count']

    def get_recipes(self, obj):
        limit = self.context['request'].query_params.get('recipes_limit')
        if limit:
            limit = int(limit)
        recipes = obj.recipes.all()[:limit] if limit else obj.recipes.all()
        return ReceiptRepresantaionSerializer(recipes, many=True).data


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = ['user', 'author']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=['user', 'author'])]

        def validate(self, data):
            if data['user'] == data['author']:
                raise serializers.ValidationError('Нельзя подписаться на себя')
            return data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['user', 'recipe']

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')

        if recipe.favorites.filter(user=user).exists():
            raise serializers.ValidationError('Уже добавлено в избранное.')
        return data

    def to_representation(self, instance):
        return ReceiptRepresantaionSerializer(instance.recipe).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ['user', 'recipe']

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')

        if recipe.shopping_carts.filter(user=user).exists():
            raise serializers.ValidationError('Уже добавлено в покупках.')
        return data

    def to_representation(self, instance):
        return ReceiptRepresantaionSerializer(instance.recipe).data
