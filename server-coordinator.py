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
        return f'{self.func}({self.funcArgs[:64]}...) = {self.result} ({self.worker.id})'

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


class Distributor():

    def __init__(self, r):
        self.redis = r

    def send_ping(self):
        self.redis.publish("lobby", 'PING')

    def send_state(self):
        self.redis.publish("lobby", 'STATE')

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
            channel = job.redis_channel()
            args = job.redis_args()
            job.worker.state = 2
            pending += [jobs.pop(i)]
            self.redis.publish(channel, args)
        return [jobs, pending]

    def __call__(self, func, argument_list):
        global job_list
        global sign_exit
        global worker_list
        global finished_job_list
        global pending_job_list

        start_flag = True
        ping_counter = 0
        state_counter = 0

        while True:

            if start_flag:
                job_list = self.create_jobs(func, argument_list)
                start_flag = False

            if ping_counter > 60:
                self.send_ping()
                ping_counter = 0

            if state_counter > 5:
                self.send_state()
                state_counter = 0

            job_list = self.map_workers_to_jobs(worker_list, job_list)
            job_list, pending_job_list = self.start_jobs(job_list, pending_job_list)

            if len(finished_job_list) == len(argument_list):
                sign_exit = True
                break

            ping_counter += 1
            state_counter += 1
            time.sleep(0.001)


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
        choices=['fibonacci', 'sleep', 'shacrack', 'shacrackprod']
    )
    parser.add_argument(
        '-p',
        '--print-amount',
        help="Print worker amount",
        action='store_true'
    )
    parser.add_argument(
        '-d',
        '--starting-delay',
        help="Starting delay",
        default=1.0,
        type=float
    )

    #arguments = ['-f', 'shacrackprod', '-w', '1', '-c', 'abcdefghiklmnopqrstuvwxz', '-l','4', '-H', '87e93406a19d11166fd4aff9addf299aad2221cbd45febc596a527b65269b78f']
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
    distributor = Distributor(r)
    distributor(args.func, argument_list)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
