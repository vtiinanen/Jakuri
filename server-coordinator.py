#!/usr/bin/env python3

"""
Coordinator server for Jakuri
"""

import sys
import argparse
import time

import redis
import shortuuid


worker_list = []
job_list = []
finished_job_list = []
number_list = [x for x in range(23, 33)]


class Job():

    def __init__(self, worker, func, args):
        self.worker = worker
        self.func = func
        self.funcArgs = args
        self.id = shortuuid.uuid()
        self.result = None

    def __repr__(self):
        return f'{self.func}({self.funcArgs}) = {self.result} ({self.worker})'

    def redis_channel(self):
        return f'{self.worker}.{self.func}'

    def redis_args(self):
        return f'{self.id} {self.funcArgs}'


class Listener():

    def __init__(self, r):
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.psubscribe(['worker-*'])

    def __call__(self):
        global finished_job_list, job_list, worker_list

        msg = self.pubsub.get_message()
        if not msg:
            return

        if msg['type'] == 'subscribe':
            return

        if msg['type'] == 'psubscribe':
            return

        if "result" in msg['channel']:
            id, result = msg['data'].split(' ')
            for index, job in enumerate(job_list):
                if id in job.id:
                    job_list[index].result = result
                    finished_job_list += [job_list.pop(index)]
                    print(repr(finished_job_list[-1]))

        if "PONG" in msg['data']:
            worker_list += [msg["channel"]]
            worker_set = set(worker_list)
            worker_list = list(worker_set)


def duplicateUntilSizesMatch(first, second):
    '''
    Duplicates the first list until bigger than the second,
    after the size exceeds the second, the first gets sliced
    to the same size
    '''
    assert len(first) > 0
    assert len(second) > 0

    if len(first) == len(second):
        return first

    if len(first) > len(second):
        return first[0:len(second)]

    if len(first) < len(second):
        return duplicateUntilSizesMatch([*first, *first], second)


class Distributor():

    def __init__(self, r):
        self.redis = r

    def send_ping(self):
        self.redis.publish("lobby", 'PING')

    def start_jobs(self, worker_amount, func):
        global job_list, worker_list

        assert worker_amount >= 0

        # prune worker list to the amount requested, amount = 0 -> use all available workers
        pruned_workers = worker_list
        if worker_amount != 0 and worker_amount < len(worker_list):
            pruned_workers = worker_list[0:worker_amount]

        # schedule jobs
        workers = duplicateUntilSizesMatch(pruned_workers, number_list)

        for item, worker in zip(number_list, workers):
            job = Job(worker, func, item)
            job_list += [job]

        # start jobs
        for job in job_list:
            self.redis.publish(job.redis_channel(), job.redis_args())


def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-w',
        '--worker-amount',
        help="Worker amount",
        default=0,
        type=int
    )
    parser.add_argument(
        '-f',
        '--func',
        help="Function to execute",
        type=str,
        default="fibonacci",
        choices=['fibonacci']
    )
    parser.add_argument(
        '-p',
        '--print-amount',
        help="Print worker amount",
        action='store_true'
    )
    args = parser.parse_args(arguments)
    d_args = vars(args)

    r = redis.Redis('127.0.0.1', decode_responses=True)
    listener = Listener(r)
    distributor = Distributor(r)

    timeStamp = int(time.time())
    firstFlag = True
    startFlag = False
    startFlagOld = False

    # main loop
    while True:

        if firstFlag == True:
            firstFlag = False
            distributor.send_ping()

        # 0.5s non-blocking delay
        now = int(time.time())
        if now - timeStamp > 0.5:
            startFlag = True

        if startFlag == True and startFlag != startFlagOld and d_args["print_amount"]:
            print(f'Workers reached: {len(worker_list)}')
            break

        if startFlag == True and startFlag != startFlagOld:
            distributor.start_jobs(d_args["worker_amount"], d_args["func"])

        startFlagOld = startFlag

        listener()

        if len(number_list) == len(finished_job_list):
            break

        time.sleep(0.001)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
