import time
import os
from mxnet import gluon
import mxnet as mx
from PIL import Image

net = gluon.model_zoo.vision.resnet50_v1(pretrained=True, root = '/tmp/')
net.hybridize(static_alloc=True, static_shape=True)
lblPath = gluon.utils.download('http://data.mxnet.io/models/imagenet/synset.txt',path='/tmp/')
with open(lblPath, 'r') as f:
    labels = [l.rstrip() for l in f]

def lambda_handler(queueL):
    pid = os.getpid()
    blobName = "img10.jpg"

    image = Image.open(blobName)
    #image.save('tempImage_'+str(pid)+'.jpeg')

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
        # print('With prob = %.5f, it contains %s' % (prob[0,i].asscalar(), labels[i]))
        inference = inference + 'With prob = %.5f, it contains %s' % (prob[0,i].asscalar(), labels[i]) + '. '
    t2 = time.time()
    queueL.put(inference)
    return inference
import multiprocessing
queue = multiprocessing.Queue()
t1 = time.time()
pids = []
for _ in range(8):
    pid = multiprocessing.Process(target=lambda_handler, args=(queue,))
    pids.append(pid)
    pid.start()
for pid in pids:
    pid.join()
t2 = time.time()
print("Handler time = ", t2-t1)
