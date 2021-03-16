#!/usr/bin/env python3

"""
Worker client for Jakuri
"""

import redis
import shortuuid
from more_itertools import nth_product

import time
from hashlib import sha256

ID = f'{shortuuid.uuid()}'


def Fibonacci(n):
    assert n >= 0
    if n == 0:
        return 0
    if n == 1 or n == 2:
        return 1
    return Fibonacci(n-1) + Fibonacci(n-2)


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


class Listener():

    def __init__(self, r):
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.psubscribe([f'worker-{ID}.*'])
        self.pubsub.subscribe(['lobby'])

    def run(self):
        global ID

        msg = self.pubsub.get_message()
        if not msg:
            return

        if msg['type'] == 'subscribe':
            return

        if msg['type'] == 'psubscribe':
            return

        if f'worker-{ID}.' in msg['channel']:
            msg['channel'] = msg['channel'].split(".")[1]

        if 'lobby' in msg['channel'] and 'PING' in msg['data']:
            self.redis.publish(f'worker-{ID}', "PONG")

        if 'fibonacci' in msg['channel']:
            args = msg['data'].split(' ')
            id = args.pop(0)
            num = args.pop(0)
            result = Fibonacci(int(num))
            self.redis.publish(f'worker-{ID}.result', f'{id} {result}')

        if 'sleep' in msg['channel']:
            id = msg['data'].split(' ')[0]
            time.sleep(2)
            self.redis.publish(f'worker-{ID}.result', f'{id} slept')

        if 'shacrack' == msg['channel']:
            args = msg['data'].split(' ')
            id = args.pop(0)
            result = Sha256Crack(args)
            self.redis.publish(f'worker-{ID}.result', f'{id} {result}')

        if 'shacrackprod' == msg['channel']:
            args = msg['data'].split(' ')
            id = args.pop(0)
            args[1] = int(args[1])
            args[2] = int(args[2])
            args[4] = int(args[4])
            result = Sha256CrackProd(*args)
            self.redis.publish(f'worker-{ID}.result', f'{id} {result}')


if __name__ == '__main__':
    r = redis.Redis('redis', decode_responses=True)
    worker = Listener(r)
    while True:
        worker.run()
        time.sleep(0.001)
