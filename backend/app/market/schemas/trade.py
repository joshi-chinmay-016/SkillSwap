from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class BuySharesRequest(BaseModel):

    mentor_id: int = Field(
        gt=0,
        description="Mentor whose shares are being purchased"
    )

    shares: int = Field(
        gt=0,
        le=100,
        description="Number of shares to buy"
    )


class BuySharesResponse(BaseModel):

    success: bool

    mentor_id: int

    shares_bought: int

    price_per_share: Decimal

    total_cost: Decimal

    wallet_balance: Decimal

    current_price: Decimal

    total_supply: int

    trade_id: int


class SellSharesRequest(BaseModel):

    mentor_id: int = Field(gt=0)

    shares: int = Field(gt=0)


class SellSharesResponse(BaseModel):

    success: bool

    mentor_id: int

    shares_sold: int

    amount_received: Decimal

    wallet_balance: Decimal

    current_price: Decimal

    remaining_shares: int

    trade_id: int