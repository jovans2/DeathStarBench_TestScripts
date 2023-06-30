import sys

sys.path.append('../gen-py')

import uuid
import random
import string
import docker
import threading
import multiprocessing
import time
import numpy as np

import grpc
from concurrent import futures

from social_network import TextService
from social_network import SocialGraphService
from social_network import UserService
from social_network import PostStorageService
from social_network import UserMentionService
from social_network import HomeTimelineService
from social_network import ComposePostService
from social_network import UrlShortenService

from social_network.ttypes import Media
from social_network.ttypes import PostType
from social_network.ttypes import Creator
from social_network.ttypes import Url
from social_network.ttypes import UserMention
from social_network.ttypes import Post
from social_network.ttypes import ServiceException
from social_network.ttypes import Url

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

addresses = {}
services = ["TextService", "SocialGraphService", "UserService", "UserMentionService", "UrlShortenService",
            "PostStorageService", "ComposePostService", "HomeTimelineService"]
for service in services:
    client = docker.DockerClient()
    container = client.containers.get(service)
    ip_add = container.attrs['NetworkSettings']['Networks']['socialnetwork_default']['IPAddress']
    addresses[service] = ip_add

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


def lambda_call_sgraph(queueL):
    t1 = time.time()
    address = addresses["SocialGraphService"]
    socket = TSocket.TSocket(address, 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = SocialGraphService.Client(protocol)

    follower = random.randint(1, 80000)
    followee = random.randint(1, 80000)
    while followee == follower:
        followee = random.randint(1, 80000)

    transport.open()
    req_id = uuid.uuid4().int & (1 << 32)
    client.Follow(req_id, follower, followee, {})

    transport.close()
    t2 = time.time()
    queueL.put(t2 - t1)
    return 0


def lambda_call_user(queueL):
    t1 = time.time()
    address = addresses["UserService"]
    socket = TSocket.TSocket(address, 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = SocialGraphService.Client(protocol)

    user = random.randint(1, 80000)

    transport.open()
    req_id = uuid.uuid4().int & (1 << 32)
    client.Login(req_id, "username_" + str(user), "password_" + str(user), {})

    transport.close()
    t2 = time.time()
    queueL.put(t2 - t1)
    return 0


duration = 10
seed = 100
rates = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200]
# generate Poisson's distribution of events
instance_events_list = []
for rate in rates:
    np.random.seed(seed)
    beta = 1.0 / rate
    oversampling_factor = 2
    inter_arrivals = list(np.random.exponential(scale=beta, size=int(oversampling_factor * duration * rate)))
    instance_events_list.append(EnforceActivityWindow(0, duration, inter_arrivals))

for repetition in range(0, 3):
    for instance_events in instance_events_list:
        queue = multiprocessing.Queue()
        print(instance_events_list.index(instance_events))
        time.sleep(10)
        after_time, before_time = 0, 0
        st = 0
        tids = []
        times = []
        for t in instance_events:
            st = st + t - (after_time - before_time)
            before_time = time.time()
            if st > 0:
                time.sleep(st)
            thread = threading.Thread(target=lambda_call_user, args=(queue,))
            thread.start()
            tids.append(thread)
            after_time = time.time()

        done = 0
        for tid in tids:
            done += 1
            if done % 1000 == 0:
                print("Done = ", done)
            tid.join(5)

        for tid in tids:
            times.append(queue.get())

        print("P50 = ", round(1000 * np.percentile(times, 50), 2), "ms")
        print("P90 = ", round(1000 * np.percentile(times, 90), 2), "ms")
        print("P99 = ", round(1000 * np.percentile(times, 99), 2), "ms")