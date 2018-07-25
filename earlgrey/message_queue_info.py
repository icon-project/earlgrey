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

from pika.adapters.blocking_connection import BlockingChannel
from aio_pika.robust_channel import RobustChannel


class MessageQueueInfoAsync:
    def __init__(self, channel: RobustChannel, route_key: str=None):
        self._channel = channel
        self._route_key = route_key

    async def queue_info(self, name: str=None):
        if name is None:
            name = self._route_key

        return await self._channel.declare_queue(name, passive=True)

    async def exchange_info(self, name: str=None):
        return await self._channel.declare_exchange(name, passive=True)


class MessageQueueInfoSync:
    def __init__(self, channel: BlockingChannel, route_key: str):
        self._channel = channel
        self._route_key = route_key

    def queue_info(self, name: str=None):
        if name is None:
            name = self._route_key

        return self._channel.queue_declare(queue=name, passive=True)

    def exchange_info(self, name: str=None):
        if name is None:
            name = self._route_key

        return self._channel.exchange_declare(exchange=name, passive=True)
