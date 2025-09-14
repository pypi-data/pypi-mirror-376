from contextlib import asynccontextmanager

from faststream import Context
from faststream.rabbit import RabbitBroker

from bovine.activitystreams.utils import is_public

from cattle_grid.dependencies import CommittingSession, CorrelationId, SqlAsyncEngine
from cattle_grid.dependencies.globals import global_container
from cattle_grid.dependencies.processing import FactoriesForActor
from cattle_grid.extensions import Extension
from cattle_grid.manage.actor import ActorManager
from cattle_grid.model import ActivityMessage

from .dependencies import PublishingActor
from .publisher import Publisher

from .config import HtmlDisplayConfiguration
from .models import Base, PublishedObject
from .router import router
from .types import NameActorMessage


@asynccontextmanager
async def lifespan(engine: SqlAsyncEngine):
    """The lifespan ensure that the necessary database table is
    created."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


extension = Extension(
    name="simple html display",
    module=__name__,
    lifespan=lifespan,
    config_class=HtmlDisplayConfiguration,
)
extension.rewrite_group_name = "html_display"
extension.rewrite_rules = {"publish_object": "html_display_publish_object"}
extension.include_router(router)


@extension.subscribe("html_display_publish_object")
async def html_publish_object(
    message: ActivityMessage,
    session: CommittingSession,
    actor: PublishingActor,
    config: extension.Config,  # type:ignore
    factories: FactoriesForActor,
    correlation_id: CorrelationId,
    broker: RabbitBroker = Context(),
):
    obj = message.data

    if not is_public(obj):
        await broker.publish(
            ActivityMessage(actor=message.actor, data=obj),
            routing_key="publish_object",
            exchange=global_container.exchange,
            correlation_id=correlation_id,
        )
        return

    if obj.get("id"):
        raise ValueError("Object ID must not be set")

    if obj.get("attributedTo") != message.actor:
        raise ValueError("Actor must match object attributedTo")

    publisher = Publisher(actor, config)
    publisher.update_object(obj)

    session.add(PublishedObject(id=publisher.uuid, data=obj, actor=actor.actor))

    activity = factories[0].create(obj).build()

    await broker.publish(
        ActivityMessage(actor=message.actor, data=activity),
        routing_key="publish_activity",
        exchange=global_container.exchange,
        correlation_id=correlation_id,
    )


@extension.subscribe("html_display_name")
async def name_actor(
    message: NameActorMessage,
    actor: PublishingActor,
    session: CommittingSession,
    config: extension.Config,  # type:ignore
):
    if message.actor != actor.actor:
        raise Exception("Actor mismatch")

    actor.name = message.name

    if config.automatically_add_users_to_group:
        manager = ActorManager(actor_id=actor.actor, session=session)
        await manager.add_to_group("html_display")
