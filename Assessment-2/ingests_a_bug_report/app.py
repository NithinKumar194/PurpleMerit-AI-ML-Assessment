def calculate_discounted_prices(cart_items):
    """
    Calculates final prices after applying discount.
    Each item is a dict with 'name', 'price', and optional 'discount_percent'.
    """
    results = []
    for item in cart_items:
        price = item['price']
        discount = item.get('discount_percent', 0.0)
        # Bug: Logic error leading to division by zero if discount is 1.0 (100%)
        # It should be: final_price = price * (1 - discount)
        final_price = price / (1 - discount) 
        results.append({
            'name': item['name'],
            'final_price': final_price
        })
    return results

if __name__ == "__main__":
    # Quick test
    items = [{'name': 'Apple', 'price': 100, 'discount_percent': 0.1}]
    print(calculate_discounted_prices(items))
