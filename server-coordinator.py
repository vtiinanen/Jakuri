#!/usr/bin/env python3

"""
Coordinator server for Jakuri
"""

import sys
import argparse
import time
import math
from threading import Thread

import redis
import shortuuid


worker_list = []
job_list = []
pending_job_list = []
finished_job_list = []
argument_list = []
sign_exit = False


class Job():

    def __init__(self, func, args):
        self.worker = None
        self.func = func
        self.funcArgs = args
        self.id = shortuuid.uuid()
        self.result = None

    def __repr__(self):
        return f'{self.func}({self.funcArgs[-64::]}) = {self.result} ({self.worker.id})'

    def redis_channel(self):
        return f'{self.worker.id}.{self.func}'

    def redis_args(self):
        return f'{self.id} {self.funcArgs}'

    def set_worker(self, worker):
        self.worker = worker


class Worker():

    def __init__(self, id):
        self.id = id
        self.state = 0

    def set_state(self, new_state):
        self.state = new_state


class Listener(Thread):

    def __init__(self, r):
        Thread.__init__(self)
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.psubscribe(['worker-*'])

    def run(self):
        global finished_job_list
        global pending_job_list
        global job_list
        global worker_list
        global sign_exit

        for msg in self.pubsub.listen():
            if not msg:
                continue

            if msg['type'] == 'subscribe':
                continue

            if msg['type'] == 'psubscribe':
                continue

            if "result" in msg['channel']:
                id, result = msg['data'].split(' ')
                for index, job in enumerate(pending_job_list):
                    if id in job.id:
                        pending_job_list[index].result = result
                        finished_job_list += [pending_job_list.pop(index)]
                        if finished_job_list[-1].result:
                            print(repr(finished_job_list[-1]))

            worker_id = msg['channel']

            if "PONG" in msg['data']:
                worker_list += [Worker(worker_id)]
                worker_list = list(set(worker_list))

            if "STATE" in msg['data']:
                state = msg['data'].split(' ')[1]
                for worker in worker_list:
                    if worker.id == worker_id:
                        worker.set_state(int(state))

            if sign_exit:
                break


class Distributor(Thread):

    def __init__(self, r, args, param_list):
        Thread.__init__(self)
        self.redis = r
        self.args = args
        self.param_list = param_list

    def send_ping(self):
        self.redis.publish("lobby", 'PING')

    def send_state(self):
        self.redis.publish("lobby", 'STATE')

    def send_job(self, job):
        channel = job.redis_channel()
        args = job.redis_args()
        self.redis.publish(channel, args)

    def create_jobs(self, func, arg_list):
        jobs = []
        for item in arg_list:
            job = Job(func, item)
            jobs += [job]
        return jobs

    def map_workers_to_jobs(self, workers, jobs):
        if not jobs:
            return
        ready_workers = [w for w in workers if w.state == 1]
        for job in jobs:
            if ready_workers:
                job.worker = ready_workers.pop()
        return jobs

    def start_jobs(self, jobs, pending):
        if not jobs:
            return [jobs, pending]
        for i, job in enumerate(jobs):
            if not job.worker:
                continue
            if job.worker.state != 1:
                continue
            job.worker.set_state(2)
            pending += [jobs.pop(i)]
            self.send_job(job)
        return [jobs, pending]

    def run(self):
        global job_list
        global sign_exit
        global worker_list
        global finished_job_list
        global pending_job_list

        start_flag = True
        now = float(time.time())
        timestamp_p = now
        timestamp_s = now
        
        while True:
            now = float(time.time())

            if sign_exit:
                break

            if start_flag:
                job_list = self.create_jobs(self.args.func, self.param_list)
                self.send_ping()
                start_flag = False

            if now - timestamp_p > 0.5:
                self.send_ping()
                timestamp_p = now

            if now - timestamp_s > 0.01:
                self.send_state()
                timestamp_s = now

            job_list = self.map_workers_to_jobs(worker_list, job_list)
            job_list, pending_job_list = self.start_jobs(job_list, pending_job_list)

            if len(finished_job_list) == len(argument_list):
                sign_exit = True
                continue


def main(arguments):
    global argument_list

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-l',
        '--length',
        help="Length",
        default=1,
        type=int
    )
    parser.add_argument(
        '-c',
        '--chars',
        help="Characters",
        default="abcdefghijklmnopqrstuvwxyz1234567890",
        type=str
    )
    parser.add_argument(
        '-H',
        '--hash',
        help="Hash input",
        type=str
    )
    parser.add_argument(
        '-i',
        '--inputfile',
        help="Input argument file",
        type=argparse.FileType('r', encoding='UTF-8'),
        required=False
    )
    parser.add_argument(
        '-f',
        '--func',
        help="Function to execute",
        type=str,
        choices=['shacrack', 'shacrackprod']
    )

    #arguments = ['-f', 'shacrackprod', '-c', 'abcdefghijklmnopqrstuvwxyz', '-l','5', '-H', '87e93406a19d11166fd4aff9addf299aad2221cbd45febc596a527b65269b78f']
    args = parser.parse_args(arguments)

    if args.inputfile != None:
        input_lines = args.inputfile.readlines()
        argument_list = [line.replace("\n", "") for line in input_lines]
        args.inputfile.close()

    if args.func == "shacrackprod":

        assert args.hash != ""

        for j in range(1, args.length + 1):

            productAmount = int(math.pow(len(args.chars), j))
            batchSize = 2**16
            batchAmount = math.ceil(productAmount / batchSize)

            for k in range(batchAmount):
                start = k * batchSize
                end = k * batchSize + batchSize
                end = productAmount if end > productAmount else end
                argument_list += [f'{args.hash} {start} {end} {args.chars} {j}']

    r = redis.Redis('127.0.0.1', decode_responses=True)
    listener = Listener(r)
    listener.start()
    distributor = Distributor(r, args, argument_list)
    distributor.start()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
