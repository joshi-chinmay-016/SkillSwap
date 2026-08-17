from pydantic import BaseModel, ConfigDict


class WalletResponse(
    BaseModel
):

    balance: int

    earned_coins: int

    spent_coins: int

    model_config = ConfigDict(from_attributes=True)