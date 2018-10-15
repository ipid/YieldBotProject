__all__ = ('HandlerInput', 'HandlerOutput', 'HandlerGenerator', 'HandlerFunc', 'ChatId', 'UserId',
           'RateLimitContainer', 'HandlerContainer', 'WorkerParam', 'MessageFunc', 'TimerContainer')

import asyncio
from typing import Callable, Generator, Union, Tuple, Dict, Any, List, Optional, Set

HandlerInput = Tuple[str, 'MessageInfo']

HandlerOutput = Union[
    str, HandlerInput
]

HandlerGenerator = Generator[
    HandlerOutput,
    HandlerInput,
    None
]

HandlerFunc = Callable[[HandlerInput], Union[
    HandlerGenerator, HandlerOutput
]]

ChatId = int

UserId = int

RateLimitContainer = Dict[UserId, List[float]]

HandlerContainer = Dict[ChatId, HandlerGenerator]

WorkerParam = Tuple[str, Dict[str, Any], asyncio.Future]

MessageFunc = Callable[[], Optional[HandlerOutput]]

TimerContainer = Set['MessageTimer']
