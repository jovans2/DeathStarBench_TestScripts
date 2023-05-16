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

    def lambda_user(self, message):
        return self.stub.LambdaUser(message)

message = pb2.Message()
client = FrontendClient(sys.argv[1],4900)
print(client.lambda_user(message))