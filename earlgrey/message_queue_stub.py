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

import functools
import inspect
import logging
import pika
import threading

from typing import TypeVar, Generic
from . import (MessageQueueConnection, MessageQueueInfoSync, MessageQueueType, MessageQueueException, worker, rpc,
               MESSAGE_QUEUE_TYPE_KEY, MESSAGE_QUEUE_PRIORITY_KEY, TASK_ATTR_DICT)

T = TypeVar('T')


class MessageQueueStub(MessageQueueConnection, Generic[T]):
    TaskType: type = object

    def __init__(self, amqp_target, route_key, username=None, password=None):
        super().__init__(amqp_target, route_key, username, password)

        if self.TaskType is object and type(self) is not MessageQueueStub:
            raise RuntimeError("MessageQueueTasks is not specified.")

        self._worker_client_async: worker.ClientAsync = None
        self._rpc_client_async: rpc.ClientAsync = None

        self._async_task = object.__new__(self.__class__.TaskType)  # not calling __init__
        self._thread_local = _Local()

    async def connect(self, connection_attempts=None, retry_delay=None):
        await super().connect(connection_attempts, retry_delay)
        await self._connect_async()
        self._register_tasks_async()

    async def _connect_async(self):
        self._worker_client_async = worker.ClientAsync(self._channel, self._route_key)
        await self._worker_client_async.initialize_queue(auto_delete=True)

        self._rpc_client_async = rpc.ClientAsync(self._channel, self._route_key)
        await self._rpc_client_async.initialize_exchange()
        await self._rpc_client_async.initialize_queue(auto_delete=True)

    def _connect_sync(self):
        credential_params = pika.PlainCredentials(self._username, self._password)
        connection_params = pika.ConnectionParameters(
            host=f'{self._amqp_target}',
            heartbeat=0,
            credentials=credential_params)
        
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()

        self._thread_local.worker_client_sync = worker.ClientSync(channel, self._route_key)
        self._thread_local.worker_client_sync.initialize_queue(auto_delete=True)

        self._thread_local.rpc_client_sync: rpc.ClientSync = rpc.ClientSync(channel, self._route_key)
        self._thread_local.rpc_client_sync.initialize_exchange()
        self._thread_local.rpc_client_sync.initialize_queue(auto_delete=True)

        self._thread_local.sync_task = object.__new__(self.__class__.TaskType)  # not calling __init__
        self._thread_local.sync_info = MessageQueueInfoSync(channel, self._route_key)

    def _register_tasks_async(self):
        for attribute_name in dir(self._async_task):
            try:
                attribute = getattr(self._async_task, attribute_name)
                task_attr: dict = getattr(attribute, TASK_ATTR_DICT)
            except AttributeError:
                pass
            else:
                func_name = f"{type(self._async_task).__name__}.{attribute_name}"

                message_queue_type = task_attr[MESSAGE_QUEUE_TYPE_KEY]
                message_queue_priority = task_attr[MESSAGE_QUEUE_PRIORITY_KEY]
                if message_queue_type == MessageQueueType.Worker:
                    binding_async_method = self._call_async_worker
                elif message_queue_type == MessageQueueType.RPC:
                    binding_async_method = self._call_async_rpc
                else:
                    raise RuntimeError(f"MessageQueueType invalid. {func_name}, {message_queue_type}")

                stub = functools.partial(binding_async_method, func_name, attribute, message_queue_priority)
                setattr(self._async_task, attribute_name, stub)

    def _register_tasks_sync(self):
        for attribute_name in dir(self._thread_local.sync_task):
            try:
                attribute = getattr(self._thread_local.sync_task, attribute_name)
                task_attr: dict = getattr(attribute, TASK_ATTR_DICT)
            except AttributeError:
                pass
            else:
                func_name = f"{type(self._thread_local.sync_task).__name__}.{attribute_name}"

                message_queue_type = task_attr[MESSAGE_QUEUE_TYPE_KEY]
                message_queue_priority = task_attr[MESSAGE_QUEUE_PRIORITY_KEY]
                if message_queue_type == MessageQueueType.Worker:
                    binding_sync_method = self._call_sync_worker
                elif message_queue_type == MessageQueueType.RPC:
                    binding_sync_method = self._call_sync_rpc
                else:
                    raise RuntimeError(f"MessageQueueType invalid. {func_name}, {message_queue_type}")

                stub = functools.partial(binding_sync_method, func_name, attribute, message_queue_priority)
                setattr(self._thread_local.sync_task, attribute_name, stub)

    async def _call_async_worker(self, func_name, func, priority, *args, **kwargs):
        params = inspect.signature(func).bind(*args, **kwargs)
        params.apply_defaults()
        await self._worker_client_async.call(func_name, kwargs=params.arguments, priority=priority)

    async def _call_async_rpc(self, func_name, func, priority, *args, **kwargs):
        params = inspect.signature(func).bind(*args, **kwargs)
        params.apply_defaults()
        result = await self._rpc_client_async.call(func_name, kwargs=params.arguments, priority=priority)
        if isinstance(result, MessageQueueException):
            logging.error(result)
            raise result
        return result

    def _call_sync_worker(self, func_name, func, priority, *args, **kwargs):
        params = inspect.signature(func).bind(*args, **kwargs)
        params.apply_defaults()
        self._thread_local.worker_client_sync.call(func_name, kwargs=params.arguments, priority=priority)

    def _call_sync_rpc(self, func_name, func, priority, *args, **kwargs):
        params = inspect.signature(func).bind(*args, **kwargs)
        params.apply_defaults()
        result = self._thread_local.rpc_client_sync.call(func_name, kwargs=params.arguments, priority=priority)
        if isinstance(result, MessageQueueException):
            logging.error(result)
            raise result
        return result

    def async_task(self) -> T:
        return self._async_task

    def sync_task(self) -> T:
        if self._thread_local.sync_task is None:
            self._connect_sync()
            self._register_tasks_sync()

        return self._thread_local.sync_task

    def sync_info(self):
        if self._thread_local.sync_info is None:
            self._connect_sync()
            self._register_tasks_sync()

        return self._thread_local.sync_info


class _Local(threading.local):
    worker_client_sync: worker.ClientSync = None
    rpc_client_sync: rpc.ClientSync = None
    sync_task = None
    sync_info: MessageQueueInfoSync = None
