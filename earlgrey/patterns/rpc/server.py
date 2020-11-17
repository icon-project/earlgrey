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

# The original codes exist in aio_pika.patterns.rpc

import time
from typing import Optional, TYPE_CHECKING

from aio_pika.channel import Channel
from aio_pika.exchange import ExchangeType
from aio_pika.message import Message, IncomingMessage
from aio_pika.patterns.base import Base

if TYPE_CHECKING:
    from aio_pika import Queue


class Server(Base):
    DLX_NAME = 'rpc.dlx'

    def __init__(self, channel: Channel, queue_name):
        self.channel = channel

        self.func_names = {}
        self.routes = {}

        self.queue_name = queue_name
        self.queue: Optional[Queue] = None

        self.dlx_exchange = None

    async def initialize_exchange(self):
        self.dlx_exchange = await self.channel.declare_exchange(
            self.DLX_NAME,
            type=ExchangeType.HEADERS,
            auto_delete=True,
        )

    async def initialize_queue(self, **kwargs):
        arguments = kwargs.pop('arguments', {}).update({
            'x-dead-letter-exchange': self.DLX_NAME,
        })

        kwargs['arguments'] = arguments

        self.queue = await self.channel.declare_queue(name=self.queue_name, **kwargs)

    def create_callback(self, func_name, func):
        if func_name in self.routes:
            raise RuntimeError(
                'Method name already used for %r' % self.routes[func_name]
            )

        self.func_names[func] = func_name
        self.routes[func_name] = func

    async def consume(self):
        await self.queue.consume(self.on_callback)

    async def on_callback(self, message: IncomingMessage):
        func_name = message.headers['FuncName']
        if func_name not in self.routes:
            return

        payload = self.deserialize(message.body)
        func = self.routes[func_name]

        try:
            result = await self._execute(func, payload)
            result = self.serialize(result)
            message_type = 'result'
        except Exception as e:
            result = self.serialize(e)
            message_type = 'error'

        result_message = Message(
            result,
            delivery_mode=message.delivery_mode,
            correlation_id=message.correlation_id,
            timestamp=time.time(),
            type=message_type,
        )

        await self.channel.default_exchange.publish(
            result_message,
            message.reply_to,
            mandatory=False
        )

        message.ack()

    async def close(self):
        if self.queue:
            await self.queue.delete()

    @staticmethod
    async def _execute(func, payload):
        return await func(**payload)


