import grpc
import time
import sys
import numpy as np
import random
import threading
from statistics import mean, median,variance,stdev
import frontend_pb2_grpc as pb2_grpc
import frontend_pb2 as pb2

MAX_MESSAGE_LENGTH = 4 * 1024 * 1024

class FrontendClient(object):
    """
    Client for gRPC functionality
    """

    def __init__(self, host, port):
        self.host = host
        self.server_port = port

        # instantiate a channel
        self.channel = grpc.insecure_channel(
            '{}:{}'.format(self.host, self.server_port),options=[
            ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
            ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
            ])

        # bind the client and the server
        self.stub = pb2_grpc.FrontendStub(self.channel)
    
    def lambda_text(self, message):
        return self.stub.LambdaText(message)
    
    def lambda_sgraph(self, message):
        return self.stub.LambdaSGraph(message)
    
    def lambda_usr(self, message):
        return self.stub.LambdaUser(message)
    
    def lambda_pststr(self, message):
        return self.stub.LambdaPstStr(message)
    
    def lambda_usrmnt(self, message):
        return self.stub.LambdaUsrMnt(message)
    
    def lambda_homet(self, message):
        return self.stub.LambdaHomeT(message)
    
    def lambda_cpost(self, message):
        return self.stub.LambdaCPost(message)
    
    def lambda_urlshort(self, message):
        return self.stub.LambdaUrlShort(message)

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

def lambda_call(lambda_m, frontend_cl):
    method = getattr(frontend_cl, lambda_m)
    message = pb2.Message()
    method(message)
    return 0

method_list = [func for func in dir(FrontendClient) if callable(getattr(FrontendClient, func))]
lambdas = []
for method in method_list:
    if "lambda" in method:
        lambdas.append(method)

lambdas = ["lambda_usr", "lambda_sgraph", "lambda_text", "lambda_usrmnt", "lambda_urlshort",
           "lambda_pststr", "lambda_cpost", "lambda_homet"]
    
duration = int(sys.argv[1])
seed = 100
rate = int(sys.argv[2])
num_VMs = int(sys.argv[3])
VM_addresses = []
for indVM in range(num_VMs):
    VM_addresses.append(sys.argv[4+indVM])
# generate Poisson's distribution of events 
inter_arrivals = []
np.random.seed(seed)
beta = 1.0/rate
oversampling_factor = 2
inter_arrivals = list(np.random.exponential(scale=beta, size=int(oversampling_factor*duration*rate)))
instance_events = EnforceActivityWindow(0,duration,inter_arrivals)

for lambda_m in lambdas:
    after_time, before_time = 0, 0
    st = 0
    tids = []
    for t in instance_events:
        st = st + t - (after_time - before_time)
        before_time = time.time()
        if st > 0:
            time.sleep(st)
        frontend_cl = FrontendClient(random.choice(VM_addresses), 4900)
        thread = threading.Thread(target=lambda_call, args=(lambda_m, frontend_cl, ))
        thread.start()
        tids.append(thread)
        after_time = time.time()

    for tid in tids:
        tid.join()