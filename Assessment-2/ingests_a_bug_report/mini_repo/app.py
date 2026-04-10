"""
mini_repo/app.py
Flask app with an intentionally introduced bug:
Missing validation for 'price' field in checkout route.
Bug introduced in v1.2.0 on 2026-04-01
"""

from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


@app.route('/products', methods=['GET'])
def products():
    return jsonify([
        {"id": 1, "name": "Widget A", "price": 9.99},
        {"id": 2, "name": "Widget B", "price": 19.99},
        {"id": 3, "name": "Broken Item"},  # ← intentionally missing 'price'
    ]), 200


@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    cart = data.get("cart", [])

    # BUG: No validation that 'price' exists in each item
    # If any item is missing 'price', this crashes with KeyError
    total = sum(item['price'] * item['qty'] for item in cart)

    return jsonify({"total": total, "status": "success"}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)