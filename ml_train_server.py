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
            print("Current P95 = ", np.percentile(timesAll, 95))

if __name__ == '__main__':
    stThr = threading.Thread(target=printLatencies)
    stThr.start()
    for _ in range(90):
        threading.Thread(target=serve).start()
    stThr.join()
