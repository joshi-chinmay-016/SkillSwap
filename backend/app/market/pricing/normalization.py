from decimal import Decimal


def normalize_rating(
    rating: float
) -> Decimal:

    rating = max(
        0,
        min(rating, 5)
    )

    return (
        Decimal(str(rating))
        / Decimal("5")
    ) * Decimal("100")


def normalize_completion_rate(
    completed: int,
    total: int
) -> Decimal:

    if total == 0:
        return Decimal("0")

    return (
        Decimal(completed)
        / Decimal(total)
    ) * Decimal("100")


def normalize_response_time(
    minutes: int
) -> Decimal:

    if minutes <= 5:
        return Decimal("100")

    if minutes >= 120:
        return Decimal("0")

    return (
        Decimal(120 - minutes)
        / Decimal("115")
    ) * Decimal("100")


def normalize_activity(
    sessions_last_30_days: int
) -> Decimal:

    score = sessions_last_30_days * 5

    return Decimal(
        min(score, 100)
    )