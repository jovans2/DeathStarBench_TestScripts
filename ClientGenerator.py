import random
import socket
import argparse
import sys
import numpy as np
import time
import multiprocessing
import threading
import requests

addresses = []
duration = 0
rps = 0
numRept = 1
timeoutTime = 1

def get_args():
    global duration
    global rps
    global addresses
    global numRept
    global timeoutTime
    """Parse commandline."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=True, help="IP address of your service")
    parser.add_argument("--duration", required=True, help="duration of your experiment")
    parser.add_argument("--rps", required=True, help="average number of requests per second (Poisson lambda)")
    parser.add_argument("--rept", default=1, required=False, help="number of repetitions")
    parser.add_argument("--timeout", default=1, required=False, help="timeout for requests")
    args = parser.parse_args()
    addrGl = args.ip
    addresses.append(addrGl)
    duration = int(args.duration)
    rps = int(args.rps)
    numRept = int(args.rept)
    timeoutTime = int(args.timeout)

get_args()

def EnforceActivityWindow(start_time, end_time, instance_events):
    events_iit = []
    events_abs = [0] + instance_events
    event_times = [sum(events_abs[:i]) for i in range(1, len(events_abs) + 1)]
    event_times = [e for e in event_times if (e > start_time) and (e < end_time)]
    try:
        events_iit = [event_times[0]] + [event_times[i] - event_times[i - 1]
                                         for i in range(1, len(event_times))]
    except:
        pass
    return events_iit


def lambda_call_sgraph(queue_l):
    global timeoutTime
    t1 = time.time()
    try:
        addr = random.choice(addresses)
        requests.get('http://' + addr + ":9999", timeout=timeoutTime)
        t2 = time.time()
        queue_l.put(t2 - t1)
    except:
        pass
    return 0


rates = [rps]
seed = 100

print(rates)

# generate Poisson's distribution of events
instance_events_list = []
for rate in rates:
    np.random.seed(seed)
    beta = 1.0 / rate
    oversampling_factor = 2
    inter_arrivals = list(np.random.exponential(scale=beta, size=int(oversampling_factor * duration * rate)))
    instance_events_list.append(EnforceActivityWindow(0, duration, inter_arrivals))

for repetition in range(0, numRept):
    for instance_events in instance_events_list:
        queue = multiprocessing.Queue()
        print(instance_events_list.index(instance_events))
        after_time, before_time = 0, 0
        st = 0
        tids = []
        times = []
        indT = 0
        for t in instance_events:
            st = st + t - (after_time - before_time)
            before_time = time.time()
            if st > 0:
                time.sleep(st)
            thread = threading.Thread(target=lambda_call_sgraph, args=(queue,))
            thread.start()
            tids.append(thread)
            after_time = time.time()
            indT += 1

        done = 0
        for tid in tids:
            done += 1
            tid.join()

        while not queue.empty():
            times.append(queue.get())

        print("P50 = ", round(1000 * np.percentile(times, 50), 2), "ms")
        print("P90 = ", round(1000 * np.percentile(times, 90), 2), "ms")
        print("P99 = ", round(1000 * np.percentile(times, 99), 2), "ms")

'''
Add Readme for experiment details:
    how many VMs of each type we need
    how to trigger load
    etc.

loads = [10, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275]
tail_42GHz = [75.09, 80.42, 88.990, 119.72, 133.83, 137.02, 139.68, 140.91, 143.76, 155.01, 217.94, 6227.24]
tail_39GHz = [81.40, 84.84, 109.60, 124.13, 134.90, 141.02, 142.85, 144.31, 146.40, 159.10, 464.59, 5595.13]
tail_35GHz = [87.78, 93.12, 129.80, 151.67, 158.45, 161.56, 163.15, 166.21, 171.64, 240.43, 5183.16, 14180]
tail_33GHz = [91.67, 99.92, 156.61, 171.63, 173.42, 174.23, 176.03, 178.51, 185.47, 617.17, 5318.13, 22105]
'''
