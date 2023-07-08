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
services = ["TextService", "SocialGraphService", "UserService", "UserMentionService", "UrlShortenService", "PostStorageService", "ComposePostService", "HomeTimelineService"]
services = ["socialnetwork_url-shorten-service_1", "socialnetwork_social-graph-service_1", "socialnetwork_social-graph-service-copy_1"]

services = ["socialnetwork_social-graph-service_1", "socialnetwork_social-graph-service-first_1", "socialnetwork_social-graph-service-second_1",
            "socialnetwork_social-graph-service-third_1", "socialnetwork_social-graph-service-fourth_1", "socialnetwork_social-graph-service-fifth_1",
            "socialnetwork_social-graph-service-sixth_1", "socialnetwork_social-graph-service-seventh_1", "socialnetwork_social-graph-service-eight_1",
            "socialnetwork_social-graph-service-ninth_1"]
services = ["socialnetwork_user-service_1"]

for service in services:
    client = docker.DockerClient()
    container = client.containers.get(service)
    ip_add = container.attrs['NetworkSettings']['Networks']['socialnetwork_default']['IPAddress']
    addresses[service] = ip_add

def EnforceActivityWindow(start_time, end_time, instance_events):
  events_iit = []
  events_abs = [0] + instance_events
  event_times = [sum(events_abs[:i]) for i in range(1, len(events_abs) + 1)]
  event_times = [e for e in event_times if (e > start_time)and(e < end_time)]
  try:
      events_iit = [event_times[0]] + [event_times[i]-event_times[i-1]
                                        for i in range(1, len(event_times))]
  except:
      pass
  return events_iit

def lambda_call_sgraph(queue):
    t1 = time.time()
    #address = addresses["socialnetwork_social-graph-service_1"]
    #address1 = addresses["socialnetwork_social-graph-service-copy_1"]
    #choice = random.randint(0,1)
    #if choice == 1:
    #    address = address1
    address = addresses[random.choice(services)]
    socket = TSocket.TSocket(address, 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = SocialGraphService.Client(protocol)

    follower = random.randint(1, 80000)
    followee = random.randint(1, 80000)
    while followee == follower:
        followee = random.randint(1, 80000)

    transport.open()
    req_id = uuid.uuid4().int & (1<<32)
    client.Follow(req_id, follower, followee, {})

    transport.close()
    t2 = time.time()
    queue.put(t2-t1)
    return 0

def lambda_call_user(queue):
    t1 = time.time()
    for _ in range(1):
        address = addresses["socialnetwork_user-service_1"]
        socket = TSocket.TSocket(address, 9090)
        transport = TTransport.TFramedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = UserService.Client(protocol)

        user = random.randint(1, 60000)
        for _ in range(1):
            transport.open()
            req_id = uuid.uuid4().int & (1<<32)
            client.Login(req_id, "username_"+str(user), "password_"+str(user), {})
            # client.RegisterUser(req_id, "first_"+str(user), "second_"+str(user), "username_"+str(user), "password_"+str(user), {})
            # print(user)
            transport.close()
    #except Exception as e:
    #    print(e)
    #    t1 -= 0.05
    t2 = time.time()
    queue.put(t2-t1)
    return 0

# lambda_call_user(1)
# exit(-1)

def lambda_call_text(lastId, queue):
    t1 = time.time()
    address = addresses["socialnetwork_text-service_1"]
    socket = TSocket.TSocket(address, 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = TextService.Client(protocol)

    text = ''.join(random.choices(string.ascii_letters + string.digits, k=256))
    # user mentions
    for _ in range(random.randint(0, 5)):
        text += ' @username_' + str(random.randint(0, 80000))
    # urls
    for _ in range(random.randint(0, 5)):
        text += ' http://' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=64))

    transport.open()
    req_id = uuid.uuid4().int & (1<<32)
    client.ComposeText(req_id, text, {})

    transport.close()
    t2 = time.time()
    queue.put(t2-t1)
    return 0

def lambda_call_url(queueL):
    t1 = time.time()
    address = addresses["socialnetwork_url-shorten-service_1"]
    socket = TSocket.TSocket(address, 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = UrlShortenService.Client(protocol)

    urls = ["Hello, world"]

    transport.open()
    req_id = uuid.uuid4().int & (1<<32)
    client.ComposeUrls(req_id, urls, {})

    transport.close()
    t2 = time.time()
    queue.put(t2-t1)
    return 0

def lambda_proxy(lastId, queue):
    sum = 0
    indX = 0
    while True:
        sum += indX
        indX += 1

duration = 50
seed = 100
rates = [20, 50, 80, 100, 120, 150, 180, 200, 220, 250, 280, 300, 320, 350, 380, 400, 420, 450, 480, 500]
rates = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200]
rates = [10, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300]
rates = [10]
all_tails = []
times = []
# generate Poisson's distribution of events
instance_events_list = []
for rate in rates:
    np.random.seed(seed)
    beta = 1.0/rate
    oversampling_factor = 2
    inter_arrivals = list(np.random.exponential(scale=beta, size=int(oversampling_factor*duration*rate)))
    instance_events_list.append(EnforceActivityWindow(0, duration, inter_arrivals))
import os
for repetition in range(0, 20):
    for instance_events in instance_events_list:
        #time.sleep(300)
        for innerLoop in range(0, 12):
            queue = multiprocessing.Queue()
            print(instance_events_list.index(instance_events))
            # time.sleep(5)
            after_time, before_time = 0, 0
            st = 0
            tids = []
            # times = []
            indT = 0
            for t in instance_events:
                st = st + t - (after_time - before_time)
                before_time = time.time()
                if st > 0:
                    time.sleep(st)

                # childPid = os.fork()
                # if childPid == 0:
                thread = threading.Thread(target=lambda_call_user, args=(queue, ))
                # thread1 = threading.Thread(target=lambda_call_user, args=(queue, ))
                thread.start()
                # thread1.start()
                # thread.join()
                # thread1.join()
                # lambda_call_user(queue)
                # exit(0)
                # tids.append(childPid)
                tids.append(thread)
                after_time = time.time()
                indT += 1
            
            # time.sleep(5)
            # done = 0
            for tid in tids:
                tid.join()
                # os.waitpid(tid, 0)
            # time.sleep(1) 
            while not queue.empty():
                # all_tails.append(queue.get())
                times.append(queue.get())

            print("P50 = ", round(1000*np.percentile(times, 50), 2), "ms")
            print("P90 = ", round(1000*np.percentile(times, 90), 2), "ms")
            print("P99 = ", round(1000*np.percentile(times, 99), 2), "ms")
        time.sleep(300)

print("All tails = ", round(1000*np.percentile(times, 90), 2), "ms")
