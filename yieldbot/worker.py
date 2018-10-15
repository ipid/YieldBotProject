__all__ = ('Worker',)

import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any, Awaitable

WORKER_NUM = 5
EMPTY_DICT = {'emptyDict': True}

class Worker:
    __slots__ = ('token', 'session', 'q', 'proxy', 'logger')

    def __init__(self,
                 token: str,
                 session: aiohttp.ClientSession,
                 proxy: Optional[str]) -> None:
        self.token = token
        self.session = session
        self.q = asyncio.Queue()
        self.proxy = proxy
        self.logger = logging.getLogger('yieldbot.worker')

    async def worker(self, method: str,
                     param: Dict[str, Any], delay: float = 0.0) -> Dict[str, Any]:
        if delay > 0:
            await asyncio.sleep(delay)

        res = EMPTY_DICT

        try:
            async with self.session.post(f'https://api.telegram.org/bot{self.token}/{method}',
                                         proxy=self.proxy, json=param) as resp:
                res: Dict[str, Any] = await resp.json()

                if not res.get('ok'):
                    reason = ''
                    if res.get('description'):
                        reason = ' due to: ' + res['description']
                    self.logger.fatal(f'Call method `{method}` failed{reason}')
        except Exception as e:
            self.logger.exception(f'\nException during calling {method}\n{e}')

        return res

    def call(self, method: str, param: Dict[str, Any], delay: float = 0.0) -> Awaitable[dict]:
        return asyncio.create_task(self.worker(method, param, delay))
