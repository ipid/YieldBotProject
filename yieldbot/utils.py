__all__ = ('MessageTimer',)

from time import time as get_time

from .type_hint import *

class MessageTimer:
    __slots__ = ('exec_time', 'interval', 'func', 'chat_id')

    def __init__(self, exec_time: float, interval: float, func: MessageFunc, chat_id: ChatId):
        self.exec_time = exec_time
        self.interval = interval
        self.func = func
        self.chat_id = chat_id

    def __bool__(self):
        return get_time() > self.exec_time

    def wind_up(self):
        self.exec_time += self.interval
