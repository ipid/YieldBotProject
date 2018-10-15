import logging
import sys

from config import *
from yieldbot import BotClient

MORNING = '''<b>✧☆ 早安问候 ☆✧</b>

ip 酱，早安哟♡
今天又是超元气的一天呢♡

今天也要好好上课哟 ww
记得带上 iPad、iPhone、充电宝和键盘
在路上可以听自己喜欢的歌曲♫
'''

def ok_bot(mpack):
    yield 'ok!'

def main():
    logging.basicConfig(level=logging.ERROR, handlers=[logging.StreamHandler(sys.stdout)])
    bc = BotClient(token=IPID_CHAN_BOT, handler=ok_bot, proxy=PROXY_URL)
    bc.add_timer(lambda:MORNING, 577174070, 86390, 1539558000)
    bc.run()

if __name__ == '__main__':
    main()