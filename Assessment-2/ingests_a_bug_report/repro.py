"""
Minimal reproduction script for:
  BUG: ZeroDivisionError when discount_percent = 1.0
  FILE: mini_repo/app.py :: calculate_discounted_prices()

Run: python repro.py
Expected: exits with non-zero code and prints ZeroDivisionError
"""
import sys
import traceback
from mini_repo.app import calculate_discounted_prices

cart = [
    {"name": "Laptop",          "price": 1500, "discount_percent": 0.2},
    {"name": "Promotional Mug", "price": 15,   "discount_percent": 1.0},  # <-- triggers bug
]

print("BUG REPRODUCTION: calling calculate_discounted_prices() with 100% discount item...")
try:
    result = calculate_discounted_prices(cart)
    print(f"UNEXPECTED SUCCESS — no error raised. Result: {result}")
    sys.exit(0)
except ZeroDivisionError as e:
    print(f"BUG REPRODUCED ✓  ZeroDivisionError: {e}")
    traceback.print_exc()
    sys.exit(1)