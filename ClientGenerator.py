import random
import socket
import sys
import numpy as np
import time
import multiprocessing
import threading
import requests

addrGl = sys.argv[1]
addresses = [addrGl]

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
    t1 = time.time()
    addr = random.choice(addresses)
    rsp = requests.get('http://' + addr + ":9999")
    print(rsp.text)
    t2 = time.time()
    queue_l.put(t2 - t1)
    return 0

duration = 10
seed = 100
rates = [10, 50, 100]
# generate Poisson's distribution of events
instance_events_list = []
for rate in rates:
    np.random.seed(seed)
    beta = 1.0 / rate
    oversampling_factor = 2
    inter_arrivals = list(np.random.exponential(scale=beta, size=int(oversampling_factor * duration * rate)))
    instance_events_list.append(EnforceActivityWindow(0, duration, inter_arrivals))

for repetition in range(0, 1):
    for instance_events in instance_events_list:
        queue = multiprocessing.Queue()
        print(instance_events_list.index(instance_events))
        time.sleep(10)
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
            tid.join(5)

        for tid in tids:
            times.append(queue.get())

        print("P50 = ", round(1000 * np.percentile(times, 50), 2), "ms")
        print("P90 = ", round(1000 * np.percentile(times, 90), 2), "ms")
        print("P99 = ", round(1000 * np.percentile(times, 99), 2), "ms")
