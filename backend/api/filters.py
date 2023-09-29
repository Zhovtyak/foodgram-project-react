from django_filters.rest_framework import FilterSet, filters, CharFilter

from recipes.models import Receipt, Tag, Ingredient


class ReceiptFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
    )
    is_favorited = filters.BooleanFilter(
        method='get_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Receipt
        fields = ('author', 'tags', )

    def get_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_carts__user=self.request.user)
        return queryset


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Ingredient
        fields = ['name']
