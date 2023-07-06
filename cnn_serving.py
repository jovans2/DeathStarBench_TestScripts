import time
import os
from mxnet import gluon
import mxnet as mx
from PIL import Image
import numpy as np
import multiprocessing
import random

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
rates = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150]
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

def lambda_handler(queueL):
    t1 = time.time()
    for indI in range(4):
        blobName = "img10.jpg"

        Image.open(blobName)

        # format image as (batch, RGB, width, height)
        img = mx.image.imread(blobName)
        img = mx.image.imresize(img, 224, 224) # resize
        img = mx.image.color_normalize(img.astype(dtype='float32')/255,
                                    mean=mx.nd.array([0.485, 0.456, 0.406]),
                                    std=mx.nd.array([0.229, 0.224, 0.225])) # normalize
        img = img.transpose((2, 0, 1)) # channel first
        img = img.expand_dims(axis=0) # batchify

        prob = net(img).softmax() # predict and normalize output
        idx = prob.topk(k=5)[0] # get top 5 result
        inference = ''
        for i in idx:
            i = int(i.asscalar())
            inference = inference + 'With prob = %.5f, it contains %s' % (prob[0,i].asscalar(), labels[i]) + '. '
    t2 = time.time()
    queueL.put(t2-t1)
    return "Ok"

def requestInference(queueG):
    queueC = multiprocessing.Queue()
    t1 = time.time()
    pids = []
    for _ in range(8):
        pid = multiprocessing.Process(target=lambda_handler, args=(queueC,))
        pids.append(pid)
        pid.start()
    for pid in pids:
        pid.join()
    t2 = time.time()
    queueG.put(t2-t1)

for repetition in range(0, 1):
    for instance_events in instance_events_list:
        for inner_loop in range(6):
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
                thread = multiprocessing.Process(target=lambda_handler, args=(queue,))
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
