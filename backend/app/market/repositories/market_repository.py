from sqlalchemy.orm import Session
from sqlalchemy import select

from app.market.models.mentor_market_state import MentorMarketState
from app.market.models.mentor_fundamentals import MentorFundamentals
from app.market.models.user_holding import UserHolding
from app.market.models.trade import Trade
from app.market.models.price_history import PriceHistory
from app.market.models.market_event import MarketEvent

def get_market_state(
    db: Session,
    mentor_id: int
):

    return (
        db.query(MentorMarketState)
        .filter(
            MentorMarketState.mentor_id == mentor_id
        )
        .first()
    )

def lock_market_state(
    db: Session,
    mentor_id: int
):

    return (
        db.query(MentorMarketState)
        .filter(
            MentorMarketState.mentor_id == mentor_id
        )
        .with_for_update()
        .first()
    )

def get_fundamentals(
    db: Session,
    mentor_id: int
):

    return (
        db.query(MentorFundamentals)
        .filter(
            MentorFundamentals.mentor_id == mentor_id
        )
        .first()
    )

def get_user_holding(
    db: Session,
    user_id: int,
    mentor_id: int
):

    return (
        db.query(UserHolding)
        .filter(
            UserHolding.user_id == user_id,
            UserHolding.mentor_id == mentor_id
        )
        .first()
    )

def create_user_holding(
    db: Session,
    holding: UserHolding
):

    db.add(holding)

    db.flush()

    return holding

def update_market_state(
    db: Session,
    market_state: MentorMarketState
):

    db.add(market_state)

    db.flush()

    return market_state

def update_user_holding(
    db: Session,
    holding: UserHolding
):

    db.add(holding)

    db.flush()

    return holding

def create_trade(
    db: Session,
    trade: Trade
):

    db.add(trade)

    db.flush()

    return trade

def create_price_history(
    db: Session,
    history: PriceHistory
):

    db.add(history)

    db.flush()

    return history

def create_market_event(
    db: Session,
    event: MarketEvent
):

    db.add(event)

    db.flush()

    return event

