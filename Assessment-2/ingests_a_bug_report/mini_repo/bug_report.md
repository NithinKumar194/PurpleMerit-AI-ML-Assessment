# Bug Report

## Title
User checkout fails with KeyError on missing 'price' field

## Description
When a user attempts to checkout with an item that has no 'price' key in the
product dictionary, the application throws an unhandled KeyError and crashes
instead of returning a proper error response.

## Expected Behavior
The checkout endpoint should return HTTP 400 with a clear error message:
"Invalid product data: missing required field 'price'"

## Actual Behavior
The server crashes with:
KeyError: 'price'
500 Internal Server Error returned to the client

## Environment
- Language: Python 3.10
- Framework: Flask 2.3.2
- OS: Ubuntu 22.04 / Windows 10
- Version: app v1.2.0 (deployed 2026-04-01)

## Reproduction Hints
- Send POST /checkout with a product dict missing the 'price' key
- Happens consistently when price field is absent
- Does not happen when price is present (even if 0)
- First reported after v1.2.0 deploy on 2026-04-01