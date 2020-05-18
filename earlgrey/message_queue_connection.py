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
import os

import aio_pika
from aio_pika.robust_connection import RobustConnection, RobustChannel
from .message_queue_info import MessageQueueInfoAsync


class MessageQueueConnection:
    def __init__(self, amqp_target, route_key, username=None, password=None):
        self._amqp_target = amqp_target
        self._route_key = route_key

        self._username = username or os.getenv("AMQP_USERNAME", "guest")
        self._password = password or os.getenv("AMQP_PASSWORD", "guest")

        self._connection: RobustConnection = None
        self._channel: RobustChannel = None

        self._async_info: MessageQueueInfoAsync = None

    async def connect(self, connection_attempts=None, retry_delay=None):
        kwargs = {}
        if connection_attempts is not None:
            kwargs['connection_attempts'] = connection_attempts
        if retry_delay is not None:
            kwargs['retry_delay'] = retry_delay

        self._connection: RobustConnection = await aio_pika.connect_robust(
            host=self._amqp_target,
            login=self._username,
            password=self._password,
            **kwargs)

        self._connection.add_close_callback(self._callback_connection_close)
        self._connection.add_reconnect_callback(self._callback_connection_reconnect_callback)

        self._channel: RobustChannel = await self._connection.channel()

        self._async_info = MessageQueueInfoAsync(self._channel, self._route_key)

    def async_info(self):
        return self._async_info

    def _callback_connection_close(self):
        pass

    def _callback_connection_reconnect_callback(self, connection: RobustConnection):
        pass
