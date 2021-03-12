#!/usr/bin/env python3

"""
Worker client for Jakuri
"""

import redis
import shortuuid

import time

ID = f'{shortuuid.uuid()}'


def Fibonacci(n):
    assert n >= 0
    if n == 0:
        return 0
    if n == 1 or n == 2:
        return 1
    return Fibonacci(n-1) + Fibonacci(n-2)


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


if __name__ == '__main__':
    r = redis.Redis('redis', decode_responses=True)
    worker = Listener(r)
    while True:
        worker.run()
        time.sleep(0.001)
