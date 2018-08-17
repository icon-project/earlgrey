# Earlgrey

Earlgrey is a python library which provides a convenient way to publish and consume messages between processes using RabbitMQ. It is abstracted to RPC pattern.

## How to use
```python
# RPC methods
class Task:
    @message_queue_task
    async def echo(self, value):
        return value

# Client stub
class Stub(MessageQueueStub[Task]):
    TaskType = Task

# Server service
class Service(MessageQueueService[Task]):
    TaskType = Task

async def run():
    route_key = 'any same string between processes'

    client = Stub('localhost', route_key)
    server = Service('localhost', route_key)

    await client.connect()
    await server.connect()

    result = await client.async_task().echo('any value')
    print(result)  # 'any value'

loop = asyncio.get_event_loop()
loop.run_until_complete(run())

```


#### Caution
Actually `MessageQueueStub` does not need exact `Task` class which has full implementation of methods. It just needs signature of methods.
```python
# client side.
class Task:
    @message_queue_task
    async def echo(self, value):
        # Just signature. It is okay. Do not need implemetation.
        # But server must have its implementation
        pass
```
