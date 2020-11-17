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

# The original codes exist in aio_pika.patterns.master

from typing import Callable
from typing import TYPE_CHECKING, Optional

from aio_pika.channel import Channel
from aio_pika.message import DeliveryMode
from aio_pika.patterns.base import Base

if TYPE_CHECKING:
    from aio_pika import Queue
    from aio_pika.message import IncomingMessage


class Server(Base):
    CONTENT_TYPE = 'application/python-pickle'
    DELIVERY_MODE = DeliveryMode.PERSISTENT

    def __init__(self, channel: Channel, queue_name):
        self.channel = channel
        self.queue_name = queue_name

        self.routes = {}
        self.queue: Optional[Queue] = None

    async def initialize_queue(self, **kwargs):
        self.queue = await self.channel.declare_queue(name=self.queue_name, **kwargs)

    def create_callback(self, func_name: str, func: Callable):
        self.routes[func_name] = func

    async def consume(self):
        await self.queue.consume(self.on_callback)

    async def on_callback(self, message: 'IncomingMessage'):
        func_name = message.headers['FuncName']
        func = self.routes.get(func_name)
        if func:
            with message.process(requeue=True, ignore_processed=True):
                data = self.deserialize(message.body)
                await self._execute(func, data)

    async def close(self):
        if self.queue:
            await self.queue.delete()

    @staticmethod
    async def _execute(func, kwargs):
        kwargs = kwargs or {}
        result = await func(**kwargs)
        return result
