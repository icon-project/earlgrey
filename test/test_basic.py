import asyncio
import time
import unittest
from earlgrey import MessageQueueStub, MessageQueueService, MessageQueueType, message_queue_task


class TestBasic(unittest.TestCase):
    def test_order(self):
        order = list(reversed(range(8)))
        def _assert_order(num):
            curr_order = order.pop()
            print(f"curr_order : {curr_order}")
            self.assertEqual(num, curr_order)

        class Task:
            @message_queue_task(type_=MessageQueueType.RPC)
            async def long_time_rpc(self, x, y):
                _assert_order(1)
                await asyncio.sleep(0.5)
                _assert_order(2)
                return x + y

            @message_queue_task(type_=MessageQueueType.Worker)
            async def long_time_work(self):
                await asyncio.sleep(0.5)
                _assert_order(6)

        class Stub(MessageQueueStub[Task]):
            TaskType = Task

        class Service(MessageQueueService[Task]):
            TaskType = Task

        async def _run():
            route_key = 'something any same string between processes you want'

            client = Stub('localhost', route_key)
            server = Service('localhost', route_key)

            await client.connect()
            await server.connect()

            _assert_order(0)
            result = await client.async_task().long_time_rpc(10, 20)
            _assert_order(3)
            self.assertEqual(result, 30)

            _assert_order(4)
            await client.async_task().long_time_work()
            _assert_order(5)

            await asyncio.sleep(1.5)
            _assert_order(7)

            self.assertEqual(0, len(order))

        loop = asyncio.get_event_loop()
        loop.run_until_complete(_run())
