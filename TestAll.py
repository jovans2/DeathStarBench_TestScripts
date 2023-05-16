import sys
sys.path.append('../gen-py')

import uuid
import random
import string

from social_network import TextService
from social_network import SocialGraphService
from social_network import UserService
from social_network import PostStorageService
from social_network import UserMentionService
from social_network import HomeTimelineService
from social_network import ComposePostService
from social_network import UrlShortenService

from social_network.ttypes import Media
from social_network.ttypes import PostType
from social_network.ttypes import Creator
from social_network.ttypes import Url
from social_network.ttypes import UserMention
from social_network.ttypes import Post
from social_network.ttypes import ServiceException
from social_network.ttypes import Url

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

class SocialGraphServices(object):

    def __init__(self): 
        self.lastId = 0
        self.lastInd = 0

    def lambda_Text(self, address):
        socket = TSocket.TSocket(address, 9090)
        transport = TTransport.TFramedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = TextService.Client(protocol)

        transport.open()

        text = ''.join(random.choices(string.ascii_letters + string.digits, k=256))
        # user mentions
        for _ in range(random.randint(0, 5)):
            text += ' @username_' + str(random.randint(0, 20))
        # urls
        for _ in range(random.randint(0, 5)):
            text += ' http://' + \
                ''.join(random.choices(string.ascii_lowercase + string.digits, k=64))

        req_id = uuid.uuid4().int & 0x7FFFFFFFFFFFFFFF
        client.ComposeText(req_id, text, {})
        transport.close()

    def lambda_SGraph(self, address):
        socket = TSocket.TSocket(address, 9090)
        transport = TTransport.TFramedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = SocialGraphService.Client(protocol)

        follower = random.randint(0, self.lastId-1)
        followee = random.randint(0, self.lastId-1)

        transport.open()
        req_id = uuid.uuid4().int & (1<<32)
        client.Follow(req_id, follower, followee, {})

        transport.close()
    
    def lambda_User(self, address):
        socket = TSocket.TSocket(address, 9090)
        transport = TTransport.TFramedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = UserService.Client(protocol)
        transport.open()
        req_id = uuid.uuid4().int & 0x7FFFFFFFFFFFFFFF
        myInd = self.lastId
        self.lastId += 1
        client.RegisterUser(req_id, "first_name_"+str(myInd), "last_name_"+str(myInd), "username_"+str(myInd), "password_"+str(myInd), {})
        transport.close()
    
    def lambda_PstStr(self, address):
        socket = TSocket.TSocket(address, 9090)
        transport = TTransport.TFramedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = PostStorageService.Client(protocol)

        transport.open()

        req_id = random.getrandbits(63)
        text = "HelloWorldAgain"
        media_0 = Media(media_id=0, media_type="PHOTO")
        media_1 = Media(media_id=1, media_type="PHOTO")
        media = [media_0, media_1]
        post_id = self.lastInd
        self.lastInd += 1
        post_type = PostType.POST
        creator = Creator(username="user_"+str(post_id), user_id=post_id)
        url_0 = Url(shortened_url="shortened_url_0", expanded_url="expanded_url_0")
        url_1 = Url(shortened_url="shortened_url_1", expanded_url="expanded_url_1")
        urls = [url_0, url_1]
        randInt1 = random.randint(0,19)
        randInt2 = random.randint(0,19)
        user_mention_0 = UserMention(user_id=randInt1, username="user_"+str(randInt1))
        user_mention_1 = UserMention(user_id=randInt2, username="user_"+str(randInt2))

        user_mentions = [user_mention_0 ,user_mention_1]
        
        post = Post(user_mentions=user_mentions, req_id=req_id, creator=creator,
            post_type=post_type, urls=urls, media=media, post_id=post_id,
            text=text)
        
        client.StorePost(req_id, post, {})
        transport.close()

    def lambda_UsrMnt(self, address):
        socket = TSocket.TSocket(address, 9090)
        transport = TTransport.TFramedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = UserMentionService.Client(protocol)

        transport.open()
        req_id = uuid.uuid4().int & 0X7FFFFFFFFFFFFFFF

        user_mentions = []
        numIter = random.randint(1, 5)

        for _ in range(numIter):
            user_mentions.append("username_"+ str(random.randint(0,self.lastId-1)))

        client.ComposeUserMentions(req_id, user_mentions, {})

        transport.close()
    
    def lambda_HomeT(self, address):
        socket = TSocket.TSocket(address, 9090)
        transport = TTransport.TFramedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = HomeTimelineService.Client(protocol)

        transport.open()
        req_id = uuid.uuid4().int & 0x7FFFFFFFFFFFFFFF
        ind = random.randint(0, self.lastId-1)
        post_id = ind
        user_id = ind
        timestamp = 2
        mnt1 = 0
        mnt2 = 0
        mnt3 = 0
        while True:
            mnt1 = random.randint(0, 20)
            if mnt1 != ind:
                break
        while True:
            mnt2 = random.randint(0, 20)
            if mnt2 != ind:
                break
        while True:
            mnt3 = random.randint(0, 20)
            if mnt3 != ind:
                break
        user_mentions = [mnt1, mnt2, mnt3]
        client.WriteHomeTimeline(req_id, post_id, user_id, timestamp, user_mentions, {})

        transport.close()
    
    def lambda_CPost(self, address):
        socket = TSocket.TSocket(address, 9090)
        transport = TTransport.TFramedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = ComposePostService.Client(protocol)

        text = ''.join(random.choices(string.ascii_letters + string.digits, k=256))
        # user mentions
        for _ in range(random.randint(0, 5)):
            text += ' @username_' + str(random.randint(0, self.lastId-1))
        # urls
        for _ in range(random.randint(0, 5)):
            text += ' http://' + \
                ''.join(random.choices(string.ascii_lowercase + string.digits, k=64))
        # media
        media_ids = []
        media_types = []
        for _ in range(random.randint(1, 5)):
            media_ids.append(int(''.join(random.choices(string.digits, k=18))))
            media_types.append("png")

        transport.open()
        req_id = uuid.uuid4().int & 0x7FFFFFFFFFFFFFFF

        post_type = PostType.POST

        user_id = random.randint(0, self.lastId-1)

        client.ComposePost(int(req_id), "username_"+str(user_id), int(user_id), text, media_ids, media_types, post_type, {})
        transport.close()

    def lambda_UrlShort(self, address):
        socket = TSocket.TSocket(address, 9090)
        transport = TTransport.TFramedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = UrlShortenService.Client(protocol)

        transport.open()
        req_id = uuid.uuid4().int & ( 1 << 32 )

        ind1 = random.randint(0, 10000)
        ind2 = random.randint(0, 10000)
        ind3 = random.randint(0, 10000)

        urls = ["https://url_"+str(ind1)+".com", "https://url_"+str(ind2)+".com", "https://url_"+str(ind3)+".com"]

        client.ComposeUrls(req_id, urls, {})
        
        transport.close()