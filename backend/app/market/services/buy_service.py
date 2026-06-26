from decimal import Decimal

from sqlalchemy.orm import Session

from app.market.repositories.market_repository import (
    lock_market_state,
    get_fundamentals,
    get_user_holding,
    create_user_holding,
    update_user_holding,
    update_market_state,
    create_trade,
    create_price_history,
    create_market_event
)

from app.market.pricing.pricing_engine import (
    calculate_price,
    calculate_buy_cost
)

from app.models.wallet import Wallet

from app.repositories.wallet_repository import (
    get_wallet_by_user,
    update_wallet
)

from app.market.models.trade import Trade
from app.market.models.user_holding import UserHolding
from app.market.models.price_history import PriceHistory
from app.market.models.market_event import MarketEvent

def buy_shares(
    db: Session,
    buyer_id: int,
    mentor_id: int,
    shares: int
):
    market = lock_market_state(
    db,
    mentor_id
)

    if market is None:
        raise ValueError(
            "Mentor market not found."
    )

    fundamentals = get_fundamentals(
    db,
    mentor_id
)

    if fundamentals is None:
        raise ValueError(
        "Fundamentals unavailable."
    )


    current_price = calculate_price(
    market.total_supply,
    Decimal(
        str(
            fundamentals.fundamentals_score
        )
    )
)

    total_cost = calculate_buy_cost(
    shares,
    market.total_supply,
    Decimal(
        str(
            fundamentals.fundamentals_score
        )
    )
    )

    wallet = get_wallet_by_user(
    db,
    buyer_id
)

    if wallet is None:
        raise ValueError(
            "Wallet not found."
        )

    if wallet.balance < total_cost:
        raise ValueError(
            "Insufficient Skill Coins."
        )
    
    wallet.balance -= total_cost

    update_wallet(
    db,
    wallet
    )

    holding = get_user_holding(
    db,
    buyer_id,
    mentor_id
    )

    if holding:

        holding.shares_owned += shares

        update_user_holding(
            db,
            holding
        )

    else:

        holding = UserHolding(
            user_id=buyer_id,
            mentor_id=mentor_id,
            shares_owned=shares
        )

        create_user_holding(
            db,
            holding
        )

    trade = Trade(

    buyer_id=buyer_id,

    mentor_id=mentor_id,

    trade_type="BUY",

    shares=shares,

    price_per_share=current_price,

    total_price=total_cost

    )

    create_trade(
        db,
        trade
    )

    market.total_supply += shares

    market.current_price = calculate_price(

    market.total_supply,

    Decimal(
        str(
            fundamentals.fundamentals_score
        )
    )
)
    
    market.version += 1

    