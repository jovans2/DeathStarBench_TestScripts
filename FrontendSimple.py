import os
import socket
import signal
import threading
import sys
sys.path.append('../gen-py')
import uuid
import random
import docker
import queue
import time
import numpy as np
import requests

from social_network import UserService

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.ext.azure import metrics_exporter

services = ["socialnetwork_user-service_1"]

headers_l = {'Metadata': 'True'}
query_params_l = {'api-version': '2019-06-01'}
endpoint_l = "http://169.254.169.254/metadata/instance"
rsp_l = requests.get(endpoint_l, headers=headers_l, params=query_params_l).json()
my_name = rsp_l["compute"]["name"]

addresses = {}
for service in services:
    client = docker.DockerClient()
    container = client.containers.get(service)
    ip_add = container.attrs['NetworkSettings']['Networks']['socialnetwork_default']['IPAddress']
    addresses[service] = ip_add
queueTimes = queue.Queue()
lockQueue = threading.Lock()

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

latency_view = view_module.View("latency_"+str(os.environ['WORKLOAD_ID']), "The distribution of the latencies",
                                [],
                                m_latency_ms,
                                aggregation_module.LastValueAggregation())

exporter = metrics_exporter.new_metrics_exporter(connection_string=os.environ['APPLICATIONINSIGHTS_CONNECTION_STRING'])

view_manager.register_view(latency_view)
view_manager.register_exporter(exporter)

output_file = open("/tmp/tailLog.log", "a")

toBeTerminated = False

def lambda_call_user():
    global addresses

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

def sendNotOK(clientSocket):
    msg = 'NotOK'
    response_headers = {
        'Content-Type': 'text/html; encoding=utf8',
        'Content-Length': len(msg),
        'Connection': 'close',
    }
    response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())

    response_proto = 'HTTP/1.1'
    response_status = '404'
    response_status_text = 'NotOK'  # this can be random

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
    global toBeTerminated
    myHost = '0.0.0.0'
    myPort = 3333

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    while True:
        (clientSocket, _) = serverSocket.accept()
        clientSocket.recv(1024)
        if not toBeTerminated:
            threading.Thread(target=sendOK, args=(clientSocket,)).start()
        else:
            threading.Thread(target=sendNotOK, args=(clientSocket,)).start()

def TailSLOThread():
    global queueTimes

    while True:
        time.sleep(2)
        currTimes = []
        lockQueue.acquire()
        while not queueTimes.empty():
            currTimes.append(queueTimes.get())
        lockQueue.release()
        if len(currTimes) == 0:
            continue
        currentTail = np.percentile(currTimes, 95)
        currentTailMs = currentTail * 1000 
        # Record the latency
        print("Current tail = ", currentTailMs)
        print(currentTailMs, file=output_file, flush=True)
        mmap1.measure_float_put(m_latency_ms, currentTailMs)

        # Insert the tag map finally
        mmap1.record(tmap1)

def EventCheckThread():
    global toBeTerminated
    while True:
        time.sleep(5)
        headers = {'Metadata': 'True'}
        query_params = {'api-version': '2020-07-01'}
        endpoint = "http://169.254.169.254/metadata/scheduledevents"
        rsp = requests.get(endpoint, headers=headers, params=query_params).json()
        rcvEvents = rsp["Events"]
        if len(rcvEvents) > 0:
            for event in rcvEvents:
                if (event["EventType"] == "Terminate") and (my_name in event["Resources"]):
                    toBeTerminated = True

def serveRequest(clientSocket):
    global queueTimes
    t1 = time.time()
    childPid = os.fork()
    if childPid == 0:
        clientSocket.recv(1024)
        lambda_call_user()
        sendOK(clientSocket)
        os._exit(os.EX_OK)
    else:
        try:
            os.waitpid(childPid, 0)
            t2 = time.time()
            lockQueue.acquire()
            queueTimes.put(t2-t1)
            lockQueue.release()
        except:
            pass
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

    # Set the thread for event checking
    threadEvents = threading.Thread(target=EventCheckThread)
    threadEvents.start()

    # If a request come, then fork.
    while True:
        (clientSocket, address) = serverSocket.accept()
        threading.Thread(target=serveRequest, args=(clientSocket, )).start()


if __name__ == "__main__":
    # main program
    serverSocket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    run()
