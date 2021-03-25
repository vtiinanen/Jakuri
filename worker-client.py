#!/usr/bin/env python3

"""
Worker client for Jakuri
"""

import time
import os
from threading import Thread
from hashlib import sha256

import redis
import shortuuid
from more_itertools import nth_product

REDIS_URL = os.environ.get("REDIS_URL")

ID = f'{shortuuid.uuid()}'
STATE = 0
CMDS = ['STATE', 'PING', 'KILL', 'SLEEP']
FUNCTIONS = ['shacrackprod', 'shacrackprod']
sign_exit = False

def Sha256Crack(args):
    result = ""
    hash = args.pop(0)
    for arg in args:
        attemptHashed = sha256(arg.encode('utf-8')).hexdigest()
        if attemptHashed == hash:
            result = arg
        if result != "":
            return result
    return result


def productBatch(start, end, chars) -> list:
    pool = []
    for i in range(start, end):
        pool += [''.join(nth_product(i, *chars))]
    return pool


def Sha256CrackProd(hash, start, end, chars, length):
    result = ""
    pList = [chars for n in range(length)]
    for p in productBatch(start, end, pList):
        result = Sha256Crack([hash, p])
        if result != "":
            return result
    return result


class CmdListener(Thread):

    def __init__(self, r):
        Thread.__init__(self)
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(['lobby'])
        self.pubsub.psubscribe([f'worker-{ID}.*'])

    def run(self):
        global ID, STATE
        global sign_exit

        for msg in self.pubsub.listen():
            if not msg:
                continue

            if msg['type'] == 'subscribe':
                continue

            if msg['type'] == 'psubscribe':
                continue

            if 'STATE' in msg['data']:
                self.redis.publish(f'worker-{ID}', f'STATE {STATE}')

            if 'PING' in msg['data']:
                self.redis.publish(f'worker-{ID}', "PONG")

            if f'worker-{ID}.' not in msg['channel']:
                continue
                
            msg['channel'] = msg['channel'].split(".")[1]

            if msg['channel'] not in CMDS:
                continue

            if 'KILL' in msg['channel']:
                STATE = 2
                sign_exit = True

            if 'SLEEP' in msg['channel']:
                STATE = 2
                id = msg['data'].split(' ')[0]
                time.sleep(2)
                self.redis.publish(f'worker-{ID}.result', f'{id} slept')

            if sign_exit:
                break

            STATE = 1


class FunctionListener(Thread):

    def __init__(self, r):
        Thread.__init__(self)
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.psubscribe([f'worker-{ID}.*'])

    def run(self):
        global ID, STATE, FUNCTIONS
        global sign_exit

        for msg in self.pubsub.listen():
            if not msg:
                continue

            if msg['type'] == 'subscribe':
                continue

            if msg['type'] == 'psubscribe':
                continue

            if f'worker-{ID}.' not in msg['channel']:
                continue

            msg['channel'] = msg['channel'].split(".")[1]

            if msg['channel'] not in FUNCTIONS:
                continue

            if 'shacrack' == msg['channel']:
                STATE = 2
                args = msg['data'].split(' ')
                id = args.pop(0)
                result = Sha256Crack(args)
                self.redis.publish(f'worker-{ID}.result', f'{id} {result}')

            if 'shacrackprod' == msg['channel']:
                STATE = 2
                args = msg['data'].split(' ')
                id = args.pop(0)
                args[1] = int(args[1])
                args[2] = int(args[2])
                args[4] = int(args[4])
                result = Sha256CrackProd(*args)
                self.redis.publish(f'worker-{ID}.result', f'{id} {result}')

            if sign_exit:
                break

            STATE = 1


if __name__ == '__main__':
    r = redis.Redis(REDIS_URL, decode_responses=True)
    workerF = FunctionListener(r)
    workerC = CmdListener(r)
    workerF.start()
    workerC.start()
    STATE = 1
