from pydantic import BaseModel


class WalletResponse(
    BaseModel
):

    balance: int

    earned_coins: int

    spent_coins: int

    class Config:

        from_attributes = True