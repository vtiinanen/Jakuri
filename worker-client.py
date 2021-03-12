#!/usr/bin/env python3

"""
Worker client for Jakuri
"""

import redis
import shortuuid

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
    hash = ""
    result = ""
    for i, arg in enumerate(args):
        if i == 0:
            hash = arg
            continue
        attemptHashed = sha256(arg.encode('utf-8')).hexdigest()
        if attemptHashed == hash:
            result = arg 
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

        if 'lobby' in msg['channel'] and 'PING' in msg['data']:
            self.redis.publish(f'worker-{ID}', "PONG")

        if 'fibonacci' in msg['channel']:
            id, arg = msg['data'].split(' ')
            result = Fibonacci(int(arg))
            self.redis.publish(f'worker-{ID}.result', f'{id} {result}')

        if 'sleep' in msg['channel']:
            id, arg = msg['data'].split(' ')
            time.sleep(2)
            self.redis.publish(f'worker-{ID}.result', f'{id} slept')

        if 'shacrack' in msg['channel']:
            id, arg = msg['data'].split(' ')
            result = Sha256Crack(arg.split(','))
            self.redis.publish(f'worker-{ID}.result', f'{id} {result}')


if __name__ == '__main__':
    r = redis.Redis('redis', decode_responses=True)
    worker = Listener(r)
    while True:
        worker.run()
        time.sleep(0.001)
