from mxnet import gluon
import mxnet as mx
import os
import socket
import signal
import threading
import sys

import multiprocessing
import time
import numpy as np

from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.ext.azure import metrics_exporter

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

duration = 100
seed = 100
rates = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]
# generate Poisson's distribution of events
instance_events_list = []
for rate in rates:
    np.random.seed(seed)
    beta = 1.0 / rate
    oversampling_factor = 2
    inter_arrivals = list(np.random.exponential(scale=beta, size=int(oversampling_factor * duration * rate)))
    instance_events_list.append(EnforceActivityWindow(0, duration, inter_arrivals))

net = gluon.model_zoo.vision.resnet50_v1(pretrained=True, root = '/tmp/')
net.hybridize(static_alloc=True, static_shape=True)
lblPath = gluon.utils.download('http://data.mxnet.io/models/imagenet/synset.txt',path='/tmp/')
with open(lblPath, 'r') as f:
    labels = [l.rstrip() for l in f]
blobName = "img10.jpg"
imgGl = mx.image.imread(blobName)

queueTimes = multiprocessing.Queue()

m_latency_ms = measure_module.MeasureFloat("repl/latency", "The latency in milliseconds per DSB request", "ms")

stats = stats_module.stats
view_manager = stats.view_manager
stats_recorder = stats.stats_recorder

prompt_measure = measure_module.MeasureInt("prompts", "number of prompts", "prompts")
prompt_view = view_module.View("prompt view", "number of prompts", [], prompt_measure,
                               aggregation_module.CountAggregation())

view_manager.register_view(prompt_view)
mmap = stats_recorder.new_measurement_map()
tmap = tag_map_module.TagMap()
mmap1 = stats_recorder.new_measurement_map()
tmap1 = tag_map_module.TagMap()

latency_view = view_module.View("latency_" + str(os.environ['WORKLOAD_ID']), "The distribution of the latencies",
                                [],
                                m_latency_ms,
                                aggregation_module.LastValueAggregation())

exporter = metrics_exporter.new_metrics_exporter(connection_string=os.environ['APPLICATIONINSIGHTS_CONNECTION_STRING'])

view_manager.register_view(latency_view)
view_manager.register_exporter(exporter)


def lambda_call_user():
    t1 = time.time()

    img = imgGl
    img = mx.image.imresize(img, 224, 224)  # resize
    img = mx.image.color_normalize(img.astype(dtype='float32') / 255,
                                   mean=mx.nd.array([0.485, 0.456, 0.406]),
                                   std=mx.nd.array([0.229, 0.224, 0.225]))  # normalize
    img = img.transpose((2, 0, 1))  # channel first
    img = img.expand_dims(axis=0)  # batchify

    prob = net(img).softmax()  # predict and normalize output
    idx = prob.topk(k=5)[0]  # get top 5 result
    inference = ''
    for i in idx:
        i = int(i.asscalar())
        inference = inference + 'With prob = %.5f, it contains %s' % (prob[0, i].asscalar(), labels[i]) + '. '

    t2 = time.time()
    queueTimes.put(t2 - t1)
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
        mmap1.measure_float_put(m_latency_ms, currentTailMs)

        # Insert the tag map finally
        mmap1.record(tmap1)
        if currentTail > threshold2 * SLO:
            mmap.measure_int_put(prompt_measure, 1)
            mmap.record(tmap)
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
        threading.Thread(target=serveRequest, args=(clientSocket,)).start()


if __name__ == "__main__":
    # main program
    serverSocket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    run()

