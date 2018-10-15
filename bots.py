import logging
import sys

from config import *
from yieldbot import BotClient

def echo_bot(mpack):
    yield mpack

def num_bot(mpack):
    msg, _ = mpack
    i = int(msg)

    while True:
        msg, _ = yield str(i)
        i += int(msg)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
    bc = BotClient(token=IPID_MISC_BOT, handler=num_bot, proxy=PROXY_URL)
    bc.add_timer(lambda:'test timer', 577174070, 1)
    bc.run()
