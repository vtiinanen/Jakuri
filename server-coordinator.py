#!/usr/bin/env python3

"""
Coordinator server for Jakuri
"""

import time
import redis
import shortuuid

worker_list = []
job_list = []
finished_job_list = []
number_list = [x for x in range(0, 32)]


class Job():

    def __init__(self, worker, func, args):
        self.worker = worker
        self.func = func
        self.funcArgs = args
        self.id = shortuuid.uuid()
        self.result = None

    def __repr__(self):
        return f'{self.func}({self.funcArgs}) = {self.result}'

    def redis_channel(self):
        return f'{self.worker}.{self.func}'

    def redis_args(self):
        return f'{self.id} {self.funcArgs}'


class Listener():

    def __init__(self, r):
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.psubscribe(['worker-*'])

    def loop(self):
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


def ensureSize(first, second):
    if len(first) == len(second):
        return first

    if len(first) > len(second):
        return first[0:len(second)]

    if len(first) < len(second):
        return ensureSize(first + first, second)


class Distributor():

    def __init__(self, r):
        self.redis = r

    def send_ping(self):
        self.redis.publish("lobby", 'PING')

    def start_jobs(self):
        global finished_job_list, job_list

        # schedule jobs
        workers = worker_list
        workers = ensureSize(workers, number_list)

        for item, worker in zip(number_list, workers):
            job = Job(worker, "fibonacci", item)
            job_list += [job]

        # start jobs
        for job in job_list:
            self.redis.publish(job.redis_channel(), job.redis_args())


if __name__ == '__main__':
    r = redis.Redis('redis', decode_responses=True)
    listener = Listener(r)
    distributor = Distributor(r)

    timeStamp = int(time.time())
    firstFlag = True
    startFlag = False
    startFlagOld = False

    while True:

        if firstFlag == True:
            firstFlag = False
            distributor.send_ping()

        timeNow = int(time.time())
        if timeNow - timeStamp > 3:
            startFlag = True

        if startFlag == True and startFlag != startFlagOld:
            distributor.start_jobs()

        startFlagOld = startFlag

        listener.loop()

        if len(number_list) == len(finished_job_list):
            break
