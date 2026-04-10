def calculate_discounted_prices(cart_items):
    results = []
    for item in cart_items:
        price = item['price']
        discount = item.get('discount_percent', 0.0)
        # Bug intentionally kept: triggers ZeroDivisionError when discount=1.0
        final_price = price / (1 - discount)   # ← keep this buggy line
        results.append({'name': item['name'], 'final_price': final_price})
    return results

if __name__ == "__main__":
    items = [
        {'name': 'Apple', 'price': 100, 'discount_percent': 0.1},
        {'name': 'Mug',   'price': 15,  'discount_percent': 1.0},
    ]
    print(calculate_discounted_prices(items))