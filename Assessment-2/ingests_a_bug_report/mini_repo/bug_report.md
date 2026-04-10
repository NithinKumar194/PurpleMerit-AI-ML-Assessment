# Bug Report: Application crashes on 100% discount items

## Description
When processing a cart that contains an item with a 100% discount
(`discount_percent = 1.0`), the application crashes completely.
This is currently blocking our promotional giveaway campaign.

## Expected Behavior
The item's final price should be calculated as `0.0`, and the rest of the
cart should process normally without any errors.

## Actual Behavior
The application raises a `ZeroDivisionError: float division by zero` and
aborts the entire cart processing task.

## Environment
- Python 3.9+
- OS: Ubuntu 22.04

## Reproduction Hints
Pass a cart item with `discount_percent = 1.0` to `calculate_discounted_prices()`.
Example:
```python
calculate_discounted_prices([{"name": "Mug", "price": 15, "discount_percent": 1.0}])
```