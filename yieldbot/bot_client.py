__all__ = ('BotClient',)

import asyncio
import logging
from time import time as get_time
from types import GeneratorType
from typing import Dict, Any

import aiohttp

from .exceptions import *
from .msg_info import *
from .type_hint import *
from .worker import *
from .utils import *

PULSE_TIMEOUT = 60

class BotClient:
    __slots__ = ('token', 'handler', 'proxy', 'worker', 'handlers',
                 'logger', 'raise_exception', 'update_offset', 'rate_limit', 'timers')

    def __init__(self, token: str, handler: HandlerFunc,
                 proxy: str, raise_exception: bool = False):
        self.token = token
        self.handler = handler
        self.proxy = proxy
        self.worker = None
        self.raise_exception = raise_exception
        self.update_offset = 0
        self.rate_limit: RateLimitContainer = {}
        self.timers = set()

        if raise_exception:
            raise ValueError('raise_exception is not supported currently.')

        self.logger: logging.Logger = logging.getLogger('yieldbot.servlog')

        # Store generator instances
        self.handlers: HandlerContainer = {}

    def run(self) -> None:
        asyncio.run(self.bot_loop())

    def add_timer(self, func: MessageFunc, chat_id: ChatId, interval: float, exec_time: float = None) -> MessageTimer:
        interval = float(interval)

        if exec_time is None:
            exec_time = get_time() + interval

        exec_time = float(exec_time)

        timer = MessageTimer(exec_time, interval, func, chat_id)
        self.timers.add(timer)

        return timer

    def remove_timer(self, timer: MessageTimer):
        self.timers.remove(timer)

    async def pulse(self):
        # TODO: It's not necessary to store a large rate_limit, so it's cleaned per 5 minutes

        while True:
            self.logger.info('Pulse')

            for timer in (x for x in self.timers if x):
                timer_res = timer.func()

                if timer_res is None:
                    pass  # Do nothing
                elif isinstance(timer_res, str) or isinstance(timer_res, tuple):
                    mpack = get_reply_from_output(timer_res)
                    self.logger.info(f'Send <{mpack}> into {timer.chat_id} during pulse')
                    self.send(timer.chat_id, mpack)
                else:
                    raise BotFatalError('Timer func should return str, tuple or None.')
                timer.wind_up()

            await asyncio.sleep(PULSE_TIMEOUT)

    async def bot_loop(self) -> None:
        asyncio.create_task(self.pulse())

        conn = aiohttp.TCPConnector(limit_per_host=8,
                                    keepalive_timeout=60)

        # Remember the session is different with Chat Session of a User.
        async with aiohttp.ClientSession(connector=conn) as session:
            self.worker = Worker(token=self.token, session=session, proxy=self.proxy)

            self.logger.info('[YieldBot] start loop...')
            while True:
                try:
                    await self.bot_loop_once()
                except BotFatalError as bot_error:
                    raise bot_error
                except Exception as e:
                    self.logger.exception(str(e))

    async def bot_loop_once(self):
        updates = await self.worker.call('getUpdates', {
            'timeout': 5, 'offset': self.update_offset
        })

        if not updates['ok']:
            self.logger.critical('Get new message failed.\nMaybe you should check you using a right param?')
            await asyncio.sleep(5)
            return

        for update in updates['result']:
            # Avoid fetching the same update
            self.update_offset = update['update_id'] + 1

            # Push message into session handler
            msg = update['message']
            user_name: str = msg["from"]["username"]
            chat_id: ChatId = msg['chat']['id']
            user_id: UserId = msg['from']['id']

            # DEBUG: log
            self.logger.info(f'<{ user_name }>: { msg["text"] }')

            # Reduce delay according to interval of messages
            if user_id not in self.rate_limit:
                # rate_limit[ last_sent, delay ]
                rlim = [get_time(), 0.0]
                self.rate_limit[user_id] = rlim
            else:
                rlim = self.rate_limit[user_id]

                # Clamp delay to be larger than 0
                rlim[1] = max(rlim[1] - (get_time() - rlim[0]), 0.0)
                rlim[0] = get_time()

            # Get output from (new or existed) handler
            if chat_id not in self.handlers:
                reply: HandlerInput = self.create_handler(chat_id, msg)
            else:
                try:
                    reply = get_reply_from_output(
                        self.handlers[chat_id].send((msg['text'], MessageInfo()))
                    )
                except StopIteration as ret_val:
                    if ret_val.value is not None:
                        raise BotFatalError("A handler can't return any value.")
                    reply = self.create_handler(chat_id, msg)

            # send reply(a tuple) as Reply(message) to the original chat
            self.logger.info(f'[YieldBot] reply: <{ reply }>, delay { rlim[1] }s')
            self.send(chat_id, reply, rlim[1])

            # Add punishment to delay
            rlim[1] += 1

    # Create handler into handlers list, and return new handler's output.
    def create_handler(self, chat_id: ChatId, msg: Dict[str, Any]) -> HandlerInput:
        handler_res = self.handler(mpack=(msg['text'], MessageInfo()))

        if isinstance(handler_res, GeneratorType):
            self.handlers[chat_id] = handler_res
            reply = get_reply_from_output(handler_res.send(None))
        else:
            reply = get_reply_from_output(handler_res)

        if reply is None:
            raise BotFatalError('Handler returns/yields invalid type')
        return reply

    def send(self, chat_id: ChatId, reply: HandlerInput, delay: float = 0.0):
        # TODO: Push message into session handler
        self.worker.call('sendMessage', {
            'chat_id': chat_id, 'text': reply[0], 'parse_mode': 'HTML'
        }, delay)

def get_reply_from_output(handler_res: HandlerOutput) -> HandlerInput:
    if isinstance(handler_res, str) and handler_res != '':
        reply = (handler_res, MessageInfo())
    elif is_res_valid_tuple(handler_res):
        # TODO: Send msg with specified type
        reply = handler_res
    else:
        raise BotFatalError('Handler returns/yields invalid type')

    return reply

def is_res_valid_tuple(handler_res):
    return isinstance(handler_res, tuple) and isinstance(handler_res[0], str) \
           and handler_res[0] != '' and isinstance(handler_res[1], MessageInfo)
