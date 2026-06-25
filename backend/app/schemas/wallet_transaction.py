from pydantic import BaseModel


class WalletTransactionResponse(
    BaseModel
):

    amount: int

    type: str

    reason: str
    class Config:

        from_attributes = True