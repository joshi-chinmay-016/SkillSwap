from decimal import Decimal

from app.market.pricing.constants import (
    BASE_PRICE,
    MIN_MULTIPLIER,
    MAX_MULTIPLIER
)

from app.market.pricing.bonding_curve import (
    bonding_multiplier
)

def fundamentals_multiplier(
    score: Decimal
) -> Decimal:

    normalized = score / Decimal("100")

    return (
        MIN_MULTIPLIER
        +
        (
            MAX_MULTIPLIER
            - MIN_MULTIPLIER
        )
        * normalized
    )

def calculate_price(
    supply: int,
    fundamentals_score: Decimal
) -> Decimal:

    price = (
        BASE_PRICE
        *
        fundamentals_multiplier(
            fundamentals_score
        )
        *
        bonding_multiplier(
            supply
        )
    )

    return price.quantize(
        Decimal("0.0001")
    )

def calculate_buy_cost(
    shares: int,
    current_supply: int,
    fundamentals_score: Decimal
) -> Decimal:

    total = Decimal("0")

    for i in range(shares):

        total += calculate_price(
            current_supply + i,
            fundamentals_score
        )

    return total.quantize(
        Decimal("0.0001")
    )


def calculate_market_cap(
    current_price: Decimal,
    supply: int
) -> Decimal:

    return (
        current_price
        * Decimal(supply)
    ).quantize(
        Decimal("0.0001")
    )