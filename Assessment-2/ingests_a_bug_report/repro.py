from mini_repo.app import calculate_discounted_prices

# Test input that will trigger the ZeroDivisionError
cart_items = [{'name': 'Apple', 'price': 100, 'discount_percent': 1.0}]  # 100% discount 

# This should raise ZeroDivisionError
print(calculate_discounted_prices(cart_items))