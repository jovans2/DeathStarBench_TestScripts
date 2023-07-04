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

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

services = ["socialnetwork_social-graph-service_1", "socialnetwork_social-graph-service-first_1", "socialnetwork_social-graph-service-second_1",
            "socialnetwork_social-graph-service-third_1", "socialnetwork_social-graph-service-fourth_1", "socialnetwork_social-graph-service-fifth_1",
            "socialnetwork_social-graph-service-sixth_1", "socialnetwork_social-graph-service-seventh_1", "socialnetwork_social-graph-service-eight_1",
            "socialnetwork_social-graph-service-ninth_1"]
addresses = {}
for service in services:
    client = docker.DockerClient()
    container = client.containers.get(service)
    ip_add = container.attrs['NetworkSettings']['Networks']['socialnetwork_default']['IPAddress']
    addresses[service] = ip_add
queueTimes = multiprocessing.Queue()

def lambda_call_sgraph():
    global addresses
    global queueTimes

    t1 = time.time()
    address = addresses[random.choice(services)]
    socketC = TSocket.TSocket(address, 9090)
    transport = TTransport.TFramedTransport(socketC)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    clientC = SocialGraphService.Client(protocol)

    follower = random.randint(1, 80000)
    followed = random.randint(1, 80000)
    while followed == follower:
        followed = random.randint(1, 80000)

    transport.open()
    req_id = uuid.uuid4().int & (1 << 32)
    clientC.Follow(req_id, follower, followed, {})

    transport.close()
    t2 = time.time()
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
        if currentTail > threshold2 * SLO:
            print("Need to scale out!")
        elif currentTail > threshold1 * SLO:
            print("Need to scale up!")

def serveRequest(clientSocket):
    clientSocket.recv(1024)
    lambda_call_sgraph()
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
