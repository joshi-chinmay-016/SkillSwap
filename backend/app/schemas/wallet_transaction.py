from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WalletTransactionResponse(BaseModel):
    id: int | None = None
    user_id: int | None = None
    amount: int
    type: str
    reason: str
    reference_id: str | None = None
    created_at: datetime | str | None = None

    model_config = ConfigDict(from_attributes=True)