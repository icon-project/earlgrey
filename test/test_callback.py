import unittest


class CallbackCollection:
    def __init__(self):
        self._cb: list = []
        self._sender = "sender"

    def add(self, cb):
        self._cb.append(cb)

    def __call__(self, *args, **kwargs):
        for cb in self._cb:
            cb(self._sender, *args, **kwargs)


class CallbackObj:
    def callback(self, sender, msg):
        print(sender, msg)


class TestCallback(unittest.TestCase):
    def test_func(self):
        collection = CallbackCollection()
        obj = CallbackObj()
        collection.add(obj.callback)
        collection("msg")
