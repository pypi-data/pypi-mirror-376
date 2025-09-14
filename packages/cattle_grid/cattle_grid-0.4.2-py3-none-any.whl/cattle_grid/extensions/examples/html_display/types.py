from pydantic import Field
from cattle_grid.model.common import WithActor


class NameActorMessage(WithActor):
    name: str = Field(description="Name for the actor")
