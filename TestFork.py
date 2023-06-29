import sys
sys.path.append('../gen-py')

import uuid
import random
import string
import docker
import multiprocessing
import time
import numpy as np

import grpc
from concurrent import futures
import frontend_pb2_grpc as pb2_grpc
import frontend_pb2 as pb2

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

def lambda_call(lambda_m, lastId):
    address = addresses["UserService"]
    socket = TSocket.TSocket(address, 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = UserService.Client(protocol)
    transport.open()
    req_id = uuid.uuid4().int & 0x7FFFFFFFFFFFFFFF
    myInd = lastId
    client.RegisterUser(req_id, "first_name_" + str(myInd), "last_name_" + str(myInd), "username_" + str(myInd),
                        "password_" + str(myInd), {})
    transport.close()
    return 0

myLambda = "lambda_usr"
duration = 20
seed = 100
rates = [20, 50, 80, 100, 120, 150, 180, 200, 220, 250, 280, 300, 320, 350, 380, 400, 420, 450, 480, 500]

# generate Poisson's distribution of events
instance_events_list = []
for rate in rates:
    np.random.seed(seed)
    beta = 1.0/rate
    oversampling_factor = 2
    inter_arrivals = list(np.random.exponential(scale=beta, size=int(oversampling_factor*duration*rate)))
    instance_events_list.append(EnforceActivityWindow(0, duration, inter_arrivals))

for instance_events in instance_events_list:
    print(instance_events_list.index(instance_events))
    time.sleep(15)
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
        thread = multiprocessing.Process(target=lambda_call, args=(myLambda, indT))
        thread.start()
        tids.append(thread)
        after_time = time.time()
        indT += 1

    for tid in tids:
        tid.join()

    print("P50 = ", round(1000*np.percentile(times, 50), 2), "ms")
    print("P90 = ", round(1000*np.percentile(times, 90), 2), "ms")
    print("P99 = ", round(1000*np.percentile(times, 99), 2), "ms")
