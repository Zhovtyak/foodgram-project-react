def forming_shopping_cart_file(recipes):
    ingredients = {}
    for recipe in recipes:
        for receipt_ingredient in recipe.receipt_ingredient.all():
            name = receipt_ingredient.ingredient.name
            amount = receipt_ingredient.amount
            measurement_unit = receipt_ingredient.ingredient.measurement_unit
            if name in ingredients:
                ingredients[name]['amount'] += amount
            else:
                ingredients[name] = {
                    'amount': amount,
                    'measurement_unit': measurement_unit
                }

    file_content = ''
    for name, details in ingredients.items():
        file_content += (
            f"{name}: {details['amount']} {details['measurement_unit']}\n")

    return file_content
