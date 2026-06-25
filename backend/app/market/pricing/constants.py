"""
Central place for all market configuration.
Changing market behaviour should only require editing this file.
"""

# Initial listing price of every mentor
BASE_PRICE = 100.0

# Total virtual shares available
MAX_SUPPLY = 1000

# Weightage for fundamentals calculation
RATING_WEIGHT = 0.40
COMPLETION_WEIGHT = 0.25
RESPONSE_WEIGHT = 0.20
ACTIVITY_WEIGHT = 0.15

# Bonding curve coefficient
CURVE_ALPHA = 0.15