from pydantic import BaseModel, ConfigDict


class WalletTransactionResponse(
    BaseModel
):

    amount: int

    type: str

    reason: str

    model_config = ConfigDict(from_attributes=True)