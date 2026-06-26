from decimal import Decimal

from app.market.pricing.constants import (
    CURVE_FACTOR
)


def bonding_multiplier(
    supply: int
) -> Decimal:

    return Decimal("1") + (
        CURVE_FACTOR
        * Decimal(supply)
    )