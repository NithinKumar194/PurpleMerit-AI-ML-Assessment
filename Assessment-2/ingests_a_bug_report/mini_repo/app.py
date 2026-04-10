def calculate_discounted_prices(cart_items):
    """
    Calculates final prices after applying discount.
    Each item is a dict with 'name', 'price', and optional 'discount_percent'.

    BUG: Uses division instead of multiplication.
    Correct formula : price * (1 - discount)
    Buggy formula   : price / (1 - discount)  <-- ZeroDivisionError when discount == 1.0
    """
    results = []
    for item in cart_items:
        price    = item['price']
        discount = item.get('discount_percent', 0.0)
        # BUG on this line (line 12):
        final_price = price / (1 - discount)
        results.append({'name': item['name'], 'final_price': final_price})
    return results


if __name__ == "__main__":
    items = [{'name': 'Apple', 'price': 100, 'discount_percent': 0.1}]
    print(calculate_discounted_prices(items))