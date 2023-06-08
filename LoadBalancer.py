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
    global times
    method = getattr(frontend_cl, lambda_m)
    message = pb2.Message()
    try:
        t1 = time.time()
        method(message)
        t2 = time.time()
        times.append(t2-t1)
    except Exception as e:
        #print(e)
        pass
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
VM_probs = []

curr = 0
for indVM in range(num_VMs):
    curr += float(sys.argv[4 + num_VMs + indVM])
    VM_probs.append(curr)

# generate Poisson's distribution of events 
inter_arrivals = []
np.random.seed(seed)
beta = 1.0/rate
oversampling_factor = 2
inter_arrivals = list(np.random.exponential(scale=beta, size=int(oversampling_factor*duration*rate)))
instance_events_normal = EnforceActivityWindow(0,duration,inter_arrivals)

inter_arrivals_slow = []
beta = 1.0/(rate/2)
inter_arrivals_slow = list(np.random.exponential(scale=beta, size=int(oversampling_factor*duration*(rate/2))))
instance_events_slow = EnforceActivityWindow(0,duration,inter_arrivals_slow)

inter_arrivals_fast = []
beta = 1.0/(rate*1.7)
inter_arrivals_fast = list(np.random.exponential(scale=beta, size=int(oversampling_factor*duration*(rate*1.7))))
instance_events_fast = EnforceActivityWindow(0,duration,inter_arrivals_fast)

instance_events_list = [instance_events_slow, instance_events_normal, instance_events_fast]

inter_arrivals = []
np.random.seed(seed)
rate = 100
beta = 1.0/rate
oversampling_factor = 2
inter_arrivals = list(np.random.exponential(scale=beta, size=int(oversampling_factor*duration*rate)))
instance_events_normal_cpost = EnforceActivityWindow(0,duration,inter_arrivals)

inter_arrivals_slow = []
rate = 250
beta = 1.0/(rate)
inter_arrivals_slow = list(np.random.exponential(scale=beta, size=int(oversampling_factor*duration*(rate))))
instance_events_slow_cpost = EnforceActivityWindow(0,duration,inter_arrivals_slow)

inter_arrivals_fast = []
rate = 500
beta = 1.0/(rate)
inter_arrivals_fast = list(np.random.exponential(scale=beta, size=int(oversampling_factor*duration*(rate))))
instance_events_fast_cpost = EnforceActivityWindow(0,duration,inter_arrivals_fast)


instance_events_list_cpost = [instance_events_slow_cpost, instance_events_normal_cpost, instance_events_fast_cpost]

for lambda_m in lambdas:
    print(lambda_m)
    time.sleep(5)
    my_list = instance_events_list
    if "cpost" in lambda_m:
        my_list = instance_events_list_cpost
    for instance_events in my_list:
        print(my_list.index(instance_events))
        time.sleep(5)
        after_time, before_time = 0, 0
        st = 0
        tids = []
        times = []
        #print(len(instance_events))
        for t in instance_events:
            st = st + t - (after_time - before_time)
            before_time = time.time()
            if st > 0:
                time.sleep(st)
            chosen_ind = 0
            rand_num = random.random()
            while (rand_num > VM_probs[chosen_ind]):
                if chosen_ind == num_VMs - 1:
                    break
                chosen_ind += 1
            #print(chosen_ind)
            frontend_cl = FrontendClient(VM_addresses[chosen_ind], 4900)
            thread = threading.Thread(target=lambda_call, args=(lambda_m, frontend_cl, ))
            thread.start()
            tids.append(thread)
            after_time = time.time()

        for tid in tids:
            tid.join()

        print("P50 = ", round(1000*np.percentile(times,50),2), "ms")
        print("P90 = ", round(1000*np.percentile(times,90),2), "ms")
        print("P99 = ", round(1000*np.percentile(times,99),2), "ms")
        # time.sleep(20)

