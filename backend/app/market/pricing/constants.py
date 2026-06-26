from decimal import Decimal

# Initial mentor listing price
BASE_PRICE = Decimal("100.00")

# Bonding curve coefficient
CURVE_FACTOR = Decimal("0.015")

# Fundamentals multiplier range
MIN_MULTIPLIER = Decimal("0.80")
MAX_MULTIPLIER = Decimal("1.50")

# Maximum normalized fundamentals score
MAX_SCORE = Decimal("100.00")
