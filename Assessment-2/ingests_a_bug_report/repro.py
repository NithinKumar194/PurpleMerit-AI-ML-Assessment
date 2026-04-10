import requests

# This script triggers the error in the checkout function by sending a product without a price.

url = 'http://localhost:5000/checkout'

# Creating a cart with a product that is missing the 'price' field
cart = [
    {"id": 1, "qty": 2},  # Widget A with price
    {"id": 3, "qty": 1},  # Broken Item without price
]

# Making a POST request to the checkout endpoint
response = requests.post(url, json={"cart": cart})

print(response.status_code)
print(response.json())