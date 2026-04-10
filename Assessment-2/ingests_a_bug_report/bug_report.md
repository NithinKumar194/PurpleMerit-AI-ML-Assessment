# Bug Report: Application crashes on 100% discount items

## Description
When processing a cart that contains an item with a 100% discount (discount_percent = 1.0), the application crashes completely. This is currently blocking our promotional giveaway campaign.

## Expected Behavior
The item's final price should be calculated as 0, and the rest of the cart should process normally without errors.

## Actual Behavior
The application stops abruptly and throws a ZeroDivisionError.

## Environment
Python 3.9+
OS: Ubuntu 22.04
