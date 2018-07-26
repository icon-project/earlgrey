import asyncio
import unittest
import multiprocessing
import random
import string
import subprocess
import traceback
import os

from earlgrey import MessageQueueStub, MessageQueueService, MessageQueueType, message_queue_task


def available_credential(username, password):
    try:
        subprocess.check_output(["rabbitmqctl", "authenticate_user", username, password])
        result = subprocess.check_output(["rabbitmqctl", "list_user_permissions", username])
        return b"/	.*	.*	.*" in result
    except Exception as e:
        traceback.print_exc()
        return False


class TestMultiprocess(unittest.TestCase):
    def test_basic(self):
        server = multiprocessing.Process(target=self._run_server)
        server.daemon = True
        server.start()

        client = multiprocessing.Process(target=self._run_client)
        client.daemon = True
        client.start()

        server.join()
        client.join()

        self.assertEqual(server.exitcode, 0)
        self.assertEqual(client.exitcode, 0)

    def test_credential_failure(self):
        random_length = random.randrange(5, 10)
        random_string = "".join(random.choice(string.ascii_letters) for _ in range(random_length))

        print(f"username : {random_string}")
        print(f"password : {random_string}")

        server = multiprocessing.Process(target=self._run_server, args=(random_string, random_string))
        server.daemon = True
        server.start()

        client = multiprocessing.Process(target=self._run_client, args=(random_string, random_string))
        client.daemon = True
        client.start()

        server.join()
        client.join()

        self.assertEqual(server.exitcode, 1)
        self.assertEqual(client.exitcode, 1)

    test_username = "test"
    test_password = "test"

    @unittest.skipUnless(available_credential(test_username, test_password),
                         f"{test_username} / {test_password} invalid")
    def test_credential_success(self):
        print(f"username : {self.test_username}")
        print(f"password : {self.test_password}")

        server = multiprocessing.Process(target=self._run_server, args=(self.test_username, self.test_password))
        server.daemon = True
        server.start()

        client = multiprocessing.Process(target=self._run_client, args=(self.test_username, self.test_password))
        client.daemon = True
        client.start()

        server.join()
        client.join()

        self.assertEqual(server.exitcode, 0)
        self.assertEqual(client.exitcode, 0)

    @unittest.skipUnless(available_credential(test_username, test_password),
                         f"{test_username} / {test_password} invalid")
    def test_credential_success_environment_variable(self):
        print(f"username : {self.test_username}")
        print(f"password : {self.test_password}")

        os.environ["AMQP_USERNAME"] = self.test_username
        os.environ["AMQP_PASSWORD"] = self.test_password

        server = multiprocessing.Process(target=self._run_server)
        server.daemon = True
        server.start()

        client = multiprocessing.Process(target=self._run_client)
        client.daemon = True
        client.start()

        server.join()
        client.join()

        self.assertEqual(server.exitcode, 0)
        self.assertEqual(client.exitcode, 0)

    def _run_server(self, username=None, password=None):
        async def _run():
            try:
                message_queue_service = Service('localhost', route_key, username, password)
                await message_queue_service.connect()
            except:
                loop.stop()
                raise

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        task = loop.create_task(_run())
        loop.run_forever()

        if task.exception():
            raise task.exception()

        print("run_server finished.")

    def _run_client(self, username=None, password=None):
        async def _run():
            try:
                message_queue_stub = Stub('localhost', route_key, username, password)
                await message_queue_stub.connect()

                result = await message_queue_stub.async_task().sum(10, 20)
                self.assertEqual(result, 30)

                result = message_queue_stub.sync_task().multiply(10, 20)
                self.assertEqual(result, 200)

                message_queue_stub.sync_task().ping(123)

                await message_queue_stub.async_task().stop()
            except:
                loop.stop()
                raise

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(_run())
        print("run_client finished.")


class Task:
    @message_queue_task
    async def sum(self, x, y):
        return x + y

    @message_queue_task
    def multiply(self, x, y):
        return x * y

    @message_queue_task(type_=MessageQueueType.Worker)
    def ping(self, value):
        print(f'value : {value}')
        assert value == 123

    @message_queue_task(type_=MessageQueueType.Worker)
    async def stop(self):
        print('stop')
        asyncio.get_event_loop().stop()


class Stub(MessageQueueStub[Task]):
    TaskType = Task


class Service(MessageQueueService[Task]):
    TaskType = Task


route_key = 'something same you want'