import queue
import time

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pandas as pd
import re
import os
import warnings
import threading
import requests

from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.tags import tag_key as tag_key_module
from opencensus.tags import tag_value as tag_value_module
from datetime import datetime
from opencensus.ext.azure import metrics_exporter

headers_l = {'Metadata': 'True'}
query_params_l = {'api-version': '2019-06-01'}
endpoint_l = "http://169.254.169.254/metadata/instance"
rsp_l = requests.get(endpoint_l, headers=headers_l, params=query_params_l).json()
my_name = rsp_l["compute"]["name"]

m_latency_ms = measure_module.MeasureFloat("repl/latency", "The latency in seconds per ML train batch", "s")

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

warnings.filterwarnings("ignore")
cleanup_re = re.compile('[^a-z]+')
timesQueue = queue.Queue()
lockQueue = threading.Lock()

def cleanup(sentence):
    sentence = sentence.lower()
    sentence = cleanup_re.sub(' ', sentence).strip()
    return sentence

def serve():
    global timesQueue
    while True:
        t1 = time.time()

        childPid = os.fork()
        if childPid == 0:
            df_name = 'minioDataset.csv'
            df_path = 'pulled_' + df_name
            df = pd.read_csv(df_path)
            df['train'] = df['Text'].apply(cleanup)

            model = LogisticRegression(max_iter=100)
            tfidf_vector = TfidfVectorizer(min_df=1000).fit(df['train'])
            train = tfidf_vector.transform(df['train'])
            model.fit(train, df['Score'])
            os._exit(os.EX_OK)
        else:
            try:
                os.waitpid(childPid, 0)
            except:
                pass
        t2 = time.time()
        lockQueue.acquire()
        timesQueue.put(t2-t1)
        lockQueue.release()

def printLatencies():
    while True:
        time.sleep(5)
        lockQueue.acquire()
        timesAll = []
        while not timesQueue.empty():
            timesAll.append(timesQueue.get())
        lockQueue.release()
        if len(timesAll) > 0:
            currentTail = np.percentile(timesAll, 95)
            print("Current P95 = ", currentTail)
            print(currentTail, file=output_file, flush=True)
            mmap1.measure_float_put(m_latency_ms, currentTail)

            # Insert the tag map finally
            mmap1.record(tmap1)

if __name__ == '__main__':
    stThr = threading.Thread(target=printLatencies)
    stThr.start()
    for _ in range(90):
        threading.Thread(target=serve).start()
    stThr.join()
