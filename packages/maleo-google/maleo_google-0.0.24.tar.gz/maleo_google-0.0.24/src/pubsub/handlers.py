from pydantic import BaseModel, ConfigDict, Field
from typing import Generic, Optional
from maleo.types.controllers.message import ReturnT, MessageController
from .config.subscription import SubscriptionConfig


class SubscriptionHandler(BaseModel, Generic[ReturnT]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: SubscriptionConfig = Field(..., description="Subscription config")
    controller: Optional[MessageController[ReturnT]] = Field(
        None, description="Optional message controller"
    )


class SubscriptionHandlers(BaseModel):
    pass
