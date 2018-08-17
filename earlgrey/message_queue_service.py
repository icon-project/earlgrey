# Copyright 2017 theloop Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
from typing import TypeVar, Generic

from . import MessageQueueConnection, MessageQueueType, MESSAGE_QUEUE_TYPE_KEY, TASK_ATTR_DICT
from .patterns import worker, rpc

T = TypeVar('T')


class MessageQueueService(MessageQueueConnection, Generic[T]):
    TaskType: type = object

    loop = asyncio.get_event_loop() or asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def __init__(self, amqp_target, route_key, username=None, password=None, **task_kwargs):
        super().__init__(amqp_target, route_key, username, password)

        if self.TaskType is object and type(self) is not MessageQueueService:
            raise RuntimeError("MessageQueueTasks is not specified.")

        self._worker_server: worker.Server = None
        self._rpc_server: rpc.Server = None

        self._task = self.__class__.TaskType(**task_kwargs)

    async def connect(self, connection_attempts=None, retry_delay=None, **kwargs):
        await super().connect(connection_attempts, retry_delay)

        self._worker_server = worker.Server(self._channel, self._route_key)
        self._rpc_server = rpc.Server(self._channel, self._route_key)

        queue = await self._channel.declare_queue(self._route_key, auto_delete=True)
        await queue.consume(self._consume, **kwargs)

        await self._serve_tasks()

    async def _serve_tasks(self):
        for attribute_name in dir(self._task):
            try:
                attribute = getattr(self._task, attribute_name)
                task_attr: dict = getattr(attribute, TASK_ATTR_DICT)
            except AttributeError:
                pass
            else:
                func_name = f"{type(self._task).__name__}.{attribute_name}"

                message_queue_type = task_attr[MESSAGE_QUEUE_TYPE_KEY]
                if message_queue_type == MessageQueueType.Worker:
                    self._worker_server.create_callback(func_name, attribute)
                elif message_queue_type == MessageQueueType.RPC:
                    self._rpc_server.create_callback(func_name, attribute)
                else:
                    raise RuntimeError(f"MessageQueueType invalid. {func_name}, {message_queue_type}")

    async def _consume(self, message):
        await self._worker_server.on_callback(message)
        await self._rpc_server.on_callback(message)

    def serve(self, **kwargs):
        self.loop.create_task(self.connect(**kwargs))

    @classmethod
    def serve_all(cls):
        cls.loop.run_forever()
