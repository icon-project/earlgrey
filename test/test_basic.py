import asyncio
import unittest
import random
import string

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
            route_key = 'any same string between processes'

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

    def test_mq_info(self):
        class Task:
            @message_queue_task(type_=MessageQueueType.Worker)
            async def work_async(self):
                pass

            @message_queue_task(type_=MessageQueueType.Worker)
            def work_sync(self):
                pass

        class Stub(MessageQueueStub[Task]):
            TaskType = Task

        class Service(MessageQueueService[Task]):
            TaskType = Task

        async def _run():
            route_key_length = random.randint(5, 10)
            route_key = ''.join(random.choice(string.ascii_letters) for _ in range(route_key_length))

            client = Stub('localhost', route_key)
            await client.connect()

            await client.async_task().work_async()
            client.sync_task().work_sync()
            await asyncio.sleep(1)

            info = await client.async_info().queue_info()
            self.assertEqual(info.declaration_result.message_count, 2)

            info = client.sync_info().queue_info()
            self.assertEqual(info.method.message_count, 2)

            server = Service('localhost', route_key)
            await server.connect()
            await asyncio.sleep(1)

            info = await client.async_info().queue_info()
            self.assertEqual(info.declaration_result.message_count, 0)

            info = client.sync_info().queue_info()
            self.assertEqual(info.method.message_count, 0)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(_run())


