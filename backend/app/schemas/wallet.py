from pydantic import BaseModel, ConfigDict


class WalletResponse(BaseModel):
    id: int | None = None
    user_id: int | None = None
    balance: int
    earned_coins: int
    spent_coins: int

    model_config = ConfigDict(from_attributes=True)