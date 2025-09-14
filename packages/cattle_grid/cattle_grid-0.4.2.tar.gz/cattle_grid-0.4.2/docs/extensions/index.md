# Extensions

!!! warning
    Still experimental

## Types of extensions

cattle_grid supports different types of extensions:

- Lookup extensions: Retrieves stuff
- Transform extensions: Takes data and harmonizes the format / adds information
- Processing extensions: When an activity is received or send, the extension does something
- API extensions: Provide something accessible via HTTP

Combining these types of extension is possible.

!!! info
    I might add a transform extension for outgoing messages. Similarly, a transform extension for messages just about to be send. This would allow one to do remote instance specific transformations.

### Types of subscriptions

Extensions can define new topics, and then perform an action when a message is received. These actions should be either to change the state of the extension, e.g. update its database, or send new messages. These messages should be send to existing topics. Extensions should not send to `incoming.#` (as it is reserved for messages received form the Fediverse), not should they send to `outgoing.#`, instead they should send to `send_message`, which will ensure proper distribution to `outgoing.#`.

However, extensions should subscribe to `outgoing.#` and `incoming.#` to process messages.

## Writing an extension

The basic implementation will be

```python
from cattle_grid.extensions import Extension

extension = Extension("some name", __name__)

...
```

By writing something as a cattle_grid extension, you can first through the lookup and transform method influence cattle_grid's behavior to e.g.

- serve archived activities (e.g. from a migrated account)
- add information to activities, e.g. label them

### Serving content

By adding

```python
@extension.get("/path/{parameter}")
async def serve_content(parameter):
    return {}
```

one can use a cattle_grid extension as one would use a FastAPI router.
By using the dependency injection, one can access various object. (See FIXME)
For example, to access the database, one would use

```python
from cattle_grid.dependencies.fastapi import SqlSession

@extension.get("/path/{parameter}")
async def serve_content(parameter, session: SqlSession):
    await session.scalar(select(MyModel.parameter == parameter))

    return serialize_to_pydantic(MyModel)
```

#### Testing

One can obtain a [TestClient][fastapi.testclient.TestClient] via

```python
from fastapi.testclient import TestClient

@pytest.fixture
def test_client():
    app = FastAPI()
    app.include_router(extension.api_router)

    return TestClient(app)
```

then proceed to write tests as usual, e.g.
`test_client.get("/url")`.

### Processing activities

By defining a subscriber

```python
@extension.subscribe("method_name")
async def my_subscriber(msg: dict):
    ...
```

you can create a subscribtion to the [ActivityExchange](../architecture/exchanges.md#types-of-exchange). The subscribtion should either be
a method name defined by your extension or a subscribtion
on a topic for processing incoming or outgoing messages, i.e.
`incoming.*` or `outgoing.*`.

#### Method Information

Subscribers to a method are automatically added to
method information. The description is either the docstring
or can be specified by adding a description argument, i.e.

```python
@extension.subscribe("method_name", description="my description")
async def my_subscriber(msg: dict):
    ...

# or

@extension.subscribe("method_name")
async def my_subscriber(msg: dict):
    """My description"""
    ...
```

The description passed as an argument takes precedence.

#### Testing

One can unit test a subscriber by just importing and calling it,
e.g.

```python
from . import my_subscriber

async def test_my_subscriber():
    await my_subscriber({"some": "data"})
```

If you wish to test using the [TestRabbitBroker][faststream.rabbit.TestRabbitBroker] following the
[faststream guide](https://faststream.ag2.ai/latest/faststream/#testing-the-service), then one can use [with_test_broker_for_extension][cattle_grid.extensions.testing.with_test_broker_for_extension].
For this one can define the broker as a fixture

```python
@pytest.fixture
async def send_message_mock():
    yield AsyncMock()

@pytest.fixture
async def test_broker(send_message_mock):
    extension.configure({"var": "value"})

    async with with_test_broker_for_extension(
        [extension], {"send_message": send_message_mock}
    ) as tbr:
        yield tbr
```

and then write a test as

```python
async def test_message_send(test_broker, send_message_mock):
    await broker.publish(
        {"my": "message"}, 
        routing_key="my_routing_key", 
        exchange=exchange
    )

    send_message_mock.assert_awaited_once()
```



### Initializing the database

Define your models using SQL Alchemy, e.g.

```python
class Base(AsyncAttrs, DeclarativeBase): ...
```

You can then obtain an sql session via

```python
from cattle_grid.dependencies import SqlSession, CommittingSession
from cattle_grid.dependencies.fastapi import SqlSession, CommittingSession
```

for use with faststream or fastapi respectively, e.g.

```python
from cattle_grid.dependencies.fastapi import SqlSession

@extension.get("/path/{parameter}")
async def serve_content(parameter, session: SqlSession):
    await session.scalar(select(MyModel.parameter == parameter))

    return serialize_to_pydantic(MyModel)
```



If you wish to create the database objects on startup, you can use

```python
@asynccontextmanager
async def lifespan(engine: SqlAsyncEngine):
    """The lifespan ensure that the necessary database table is
    created."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


extension = Extension(
    name="database example",
    module=__name__,
    lifespan=lifespan)
```


### Running extensions

In order to test extensions, one might want to run these using a separate
process. This can be achieved by running

```bash
python -m cattle_grid.extensions run your.extension.module
```

See [below](#python-m-cattle_gridextensions-run) for further details on
this command.

!!! tip
    To run in your host environment change the port with `--port 8000`.

!!! warning
    This only works for processing and API extensions. Transformation
    and lookup extensions are called by cattle_grid directly.

We note here that the configuration will be loaded through
the same mechanism as cattle_grid does. This is in particular
relevant for accessing the database and the RabbitMQ router.

## Configuring extensions

Extensions are configured in `cattle_grid.toml` by adding an entry of the form

```toml
[[extensions]]

module_name = "your.extension"
config = { var = 1}

lookup_order = 2
```

The factory method in the python module `your.extension` will be called with the contents `config` as an argument.

::: mkdocs-click
    :module: cattle_grid.extensions.__main__
    :command: main
    :prog_name: python -m cattle_grid.extensions
    :depth: 1
    :list_subcommands: True
    :style: table
