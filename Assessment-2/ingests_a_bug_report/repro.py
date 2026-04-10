import sys
from mini_repo.app import calculate_discounted_prices
try:
    calculate_discounted_prices([{'name':'Mug','price':15,'discount_percent':1.0}])
except ZeroDivisionError:
    print('BUG REPRODUCED')
    sys.exit(1)