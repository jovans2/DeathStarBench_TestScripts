import os
import socket
import signal
import threading
import sys
sys.path.append('../gen-py')
import uuid
import random
import string
import docker
import multiprocessing
import time
import numpy as np

from social_network import SocialGraphService
from social_network import UserService

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.tags import tag_key as tag_key_module
from opencensus.tags import tag_value as tag_value_module
from datetime import datetime
from opencensus.ext.azure import metrics_exporter

services = ["socialnetwork_social-graph-service_1", "socialnetwork_social-graph-service-first_1", "socialnetwork_social-graph-service-second_1",
            "socialnetwork_social-graph-service-third_1", "socialnetwork_social-graph-service-fourth_1", "socialnetwork_social-graph-service-fifth_1",
            "socialnetwork_social-graph-service-sixth_1", "socialnetwork_social-graph-service-seventh_1", "socialnetwork_social-graph-service-eight_1",
            "socialnetwork_social-graph-service-ninth_1"]
services = ["socialnetwork_user-service_1"]

addresses = {}
for service in services:
    client = docker.DockerClient()
    container = client.containers.get(service)
    ip_add = container.attrs['NetworkSettings']['Networks']['socialnetwork_default']['IPAddress']
    addresses[service] = ip_add
queueTimes = multiprocessing.Queue()

m_latency_ms = measure_module.MeasureFloat("repl/latency", "The latency in milliseconds per DSB request", "ms")

stats = stats_module.stats
view_manager = stats.view_manager
stats_recorder = stats.stats_recorder

prompt_measure = measure_module.MeasureInt("prompts", "number of prompts", "prompts")
prompt_view = view_module.View("prompt view", "number of prompts", [], prompt_measure, aggregation_module.CountAggregation())

view_manager.register_view(prompt_view)
mmap = stats_recorder.new_measurement_map()
tmap = tag_map_module.TagMap()
mmap1 = stats_recorder.new_measurement_map()
tmap1 = tag_map_module.TagMap()

# Create the tag key
# key_method = tag_key_module.TagKey("method")
# Create the status key
# key_status = tag_key_module.TagKey("status")
# Create the error key
# key_error = tag_key_module.TagKey("error")

latency_view = view_module.View("latency_"+str(os.environ['WORKLOAD_ID']), "The distribution of the latencies",
    #[key_method, key_status, key_error],
    [],
    m_latency_ms,
    # Latency in buckets:
    # [>=0ms, >=25ms, >=50ms, >=75ms, >=100ms, >=200ms, >=400ms, >=600ms, >=800, >=1000]
    #aggregation_module.DistributionAggregation([0, 25, 50, 75, 100, 200, 400, 600, 800, 1000]))
    aggregation_module.LastValueAggregation())

# exporter = metrics_exporter.new_metrics_exporter(connection_string='InstrumentationKey=080046f1-79d3-48ce-8abc-1d58acb0504a;IngestionEndpoint=https://westus2-2.in.applicationinsights.azure.com/;LiveEndpoint=https://westus2.livediagnostics.monitor.azure.com/')
exporter = metrics_exporter.new_metrics_exporter(connection_string=os.environ['APPLICATIONINSIGHTS_CONNECTION_STRING'])

view_manager.register_view(latency_view)
view_manager.register_exporter(exporter)

def lambda_call_user():
    global addresses
    global queueTimes
    
    t1 = time.time()
    address = addresses[random.choice(services)]
    socketC = TSocket.TSocket(address, 9090)
    transport = TTransport.TFramedTransport(socketC)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    clientC = UserService.Client(protocol)

    follower = random.randint(1, 80000)
    
    transport.open()
    req_id = uuid.uuid4().int & (1 << 32)
    clientC.Login(req_id, "user_"+str(follower), "pass_"+str(follower), {})

    transport.close()
    t2 = time.time()

    end_ms = (t2 - t1) * 1000.0 # Seconds to milliseconds

    # Record the latency
    # mmap1.measure_float_put(m_latency_ms, end_ms)

    # tmap1.insert(key_method, tag_value_module.TagValue("repl"))
    # tmap1.insert(key_status, tag_value_module.TagValue("OK"))

    # Insert the tag map finally
    # mmap1.record(tmap1)
    # metrics1 = list(mmap1.measure_to_view_map.get_metrics(datetime.utcnow()))
    # print("Latency = ", end_ms)
    # print(metrics1)

    queueTimes.put(t2-t1)
    return 0

def signal_handler(sig, frame):
    serverSocket_.close()
    sys.exit(0)

def sendOK(clientSocket):
    msg = 'OK'
    response_headers = {
        'Content-Type': 'text/html; encoding=utf8',
        'Content-Length': len(msg),
        'Connection': 'close',
    }
    response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())

    response_proto = 'HTTP/1.1'
    response_status = '200'
    response_status_text = 'OK'  # this can be random

    # sending all this stuff
    r = '%s %s %s\r\n' % (response_proto, response_status, response_status_text)
    try:
        clientSocket.send(r.encode(encoding="utf-8"))
        clientSocket.send(response_headers_raw.encode(encoding="utf-8"))
        clientSocket.send('\r\n'.encode(encoding="utf-8"))  # to separate headers from body
        clientSocket.send(msg.encode(encoding="utf-8"))
        clientSocket.close()
    except:
        clientSocket.close()

def HealthThread():
    myHost = '0.0.0.0'
    myPort = 3333

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    while True:
        (clientSocket, _) = serverSocket.accept()
        clientSocket.recv(1024)
        threading.Thread(target=sendOK, args=(clientSocket,)).start()

def TailSLOThread():
    global queueTimes

    SLO = 0.15
    threshold1 = 0.7
    threshold2 = 0.8
    while True:
        time.sleep(2)
        currTimes = []
        while not queueTimes.empty():
            currTimes.append(queueTimes.get())
        if len(currTimes) == 0:
            continue
        currentTail = np.percentile(currTimes, 95)
        currentTailMs = currentTail * 1000 
        # Record the latency
        print("Current tail = ", currentTailMs)
        print(currentTailMs, end="", file="/tmp/tailLat.log", flush=True)
        mmap1.measure_float_put(m_latency_ms, currentTailMs)

        # tmap1.insert(key_method, tag_value_module.TagValue("repl"))
        # tmap1.insert(key_status, tag_value_module.TagValue("OK"))

        # Insert the tag map finally
        mmap1.record(tmap1)
        if currentTail > threshold2 * SLO:
            # print("Need to scale out!")
            mmap.measure_int_put(prompt_measure, 1)
            mmap.record(tmap)
            metrics = list(mmap.measure_to_view_map.get_metrics(datetime.utcnow()))
            # print(metrics)
            # print(metrics[0].time_series[0].points[0])
        elif currentTail > threshold1 * SLO:
            print("Need to scale up!")

def serveRequest(clientSocket):
    clientSocket.recv(1024)
    lambda_call_user()
    sendOK(clientSocket)
    return 0

def run():
    global serverSocket_

    # Set the address and port, the port can be acquired from environment variable
    myHost = '0.0.0.0'
    myPort = int(os.environ.get('PORT', 9999))

    # Bind the address and port
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    # Set the signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Set the thread for Health Check
    threadHealth = threading.Thread(target=HealthThread)
    threadHealth.start()

    # Set the thread for Tail Latency monitoring
    threadTailSLO = threading.Thread(target=TailSLOThread)
    threadTailSLO.start()

    # If a request come, then fork.
    while True:
        (clientSocket, address) = serverSocket.accept()
        threading.Thread(target=serveRequest, args=(clientSocket, )).start()


if __name__ == "__main__":
    # main program
    serverSocket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    run()
