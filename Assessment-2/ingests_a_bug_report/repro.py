import requests

# Testing endpoint that triggers the KeyError
url = 'http://127.0.0.1:5000/checkout'

# Sending a cart with an item that is missing the 'price' field
cart_data = {
    'cart': [
        {'id': 1, 'qty': 2},  # Widget A
        {'id': 2, 'qty': 1},  # Widget B
        {'id': 3, 'qty': 1}   # Broken Item (missing 'price')
    ]
}

response = requests.post(url, json=cart_data)
print(response.status_code, response.text)  # This should trigger the error