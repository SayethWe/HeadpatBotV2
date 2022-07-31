from __future__ import annotations #allows factory type annotations
from enum import Enum
import os, logging
from math import sqrt
import images
import pickle
from polls import Poll, Waifu
from headpatExceptions import *
import matplotlib.pyplot as plt
import numpy as np

SAVE_FOLDER = os.path.join('guilds')
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)
logger = logging.getLogger(os.environ['LOGGER_NAME'])

class ServerOption(Enum):
        PollWaifuCount=('poll waifu count',8,2,24) #how many waifus to put in a poll
        PollWaifuImageSizePixels=('poll waifu image vertical pixels',500,100,800) #how many pixels to make the tiles in the poll collage, unused
        PollWaifuImageAspect=('poll waifu image aspect percent',100,50,200)#width/height*100, unused
        GachaMaxWaifus=('gacha collection max count',8,0,25)
        GachaExpiryHours=('gacha collection expiration hours',150,5,10000)

        @staticmethod
        def defaultOptions() -> dict[str,int]:
            options=dict[str,int]()
            for option in ServerOption:
                options[option.value[0]]=option.value[1]
            return options

        @property
        def defaultValue(self) -> int:
            return self.value[1]

        @property
        def key(self) -> str:
            return self.value[0]

        @property
        def min(self) -> int:
            return self.value[2]

        @property
        def max(self) -> int:
            return self.value[3]

class Server:
    def __init__(self,identity):
        self.identity = identity
        self.waifus=list[Waifu]()
        self.polls=list[Poll]()
        self.options=ServerOption.defaultOptions()
        self.tickets=dict[int,int]()

    def getStorageDict(self):
        store = {}
        store["identity"]=self.identity
        store["waifus"]=[waifu.getStorageDict() for waifu in self.waifus]
        store["polls"] =[poll.getStorageDict() for poll in self.polls]
        store["options"]=self.options
        store["tickets"]=self.tickets
        return store

    @staticmethod
    def buildFromDict(serverDict:dict) -> Server:
        loaded=Server(serverDict["identity"])
        waifus=serverDict.get("waifus",[])
        #logger.debug(str(waifus))
        loaded.waifus=[Waifu.buildFromDict(waifuDict) for waifuDict in waifus]
        polls=serverDict.get("polls",[])
        #logger.debug(str(polls))
        loaded.polls=[Poll.buildFromDict(pollDict) for pollDict in polls]
        loaded.options=serverDict.get("options",loaded.options)
        loaded.tickets=serverDict.get("tickets",loaded.tickets)
        return loaded

    class ServerOption(Enum):
        #need to stick around for backward compatibility. Figure out how to get rid of these in stored guilds. all unused except when unpickling
        PollWaifuCount='pollSize' #how many waifus to put in a poll
        PollParticipationCheckStartHours='pollCheckZero' #when to start checking for poll participations
        PollParticipationCheckDeltaHours='pollCheckDelta' #how often to check poll participation
        PollEndHours='pollForceEnd' #when to stop checkign and just end the poll
        PollParticipationCheckCount='pollParticipation' #how many people should vote to end poll
        PollWaifuImageSizePixels='waifuImageSize' #how many pixels to make the tiles in the poll collage, unused
        PollStartNextGapHours='pollNextDelay' #how long to wait after endeing a poll to start the next, unused
        GachaMaxWaifus='gachaMaximumCollection'
        GachaExpiryHours='gachaExpiryTime'

    def getOption(self,option:ServerOption) -> int:
        try:
            return self.options[option.key]
        except AttributeError:
            self.options = ServerOption.defaultOptions()
        except KeyError:
            self.options[option.key]=option.defaultValue
        return self.options[option.key]

    def setOption(self,option:ServerOption,value:int):
        if value < option.min or value > option.max:
            raise InvalidOptionValueError
        self.options[option.key]=value

    def addWaifu(self,name:str,source:str):
        if os.path.exists(os.path.join(images.POLL_FOLDER,images.sourceNameFolder(name,source))):
            #full database has waifu
            try:
                self.getWaifuByNameSource(name,source)
                raise WaifuConflictError
            except WaifuDNEError:
                #server does not have waifu
                newWaifu = Waifu(name,source,1)
                self.waifus.append(newWaifu)
                return newWaifu
        else:
            raise WaifuDNEError
    
    def removeWaifu(self,name:str,source:str):
        toRemove=self.getWaifuByNameSource(name,source)
        self.waifus.remove(toRemove)

    def save(self):
        filePath=os.path.join(SAVE_FOLDER,f'{self.identity}.p')
        with open(filePath,'wb') as saveFile:
            try:
                pickle.dump(self,saveFile)
            except Exception as err:
                logger.error(f'failed to pickle {self} with {err}')

    @property
    def asBytes(self):
        try:
            return pickle.dumps(self)
        except Exception as err:
            logger.error(f'failed to pickle {self} with {err}')

    def delete(self):
        filePath=os.path.join(SAVE_FOLDER,f'{self.identity}.p')
        os.remove(filePath)

    @staticmethod
    def load(identity:int) -> Server:
        try:
            with open(os.path.join(SAVE_FOLDER,f'{identity}.p'),'rb') as loadFile:
                loaded = pickle.load(loadFile)
        except FileNotFoundError:
            loaded=Server(identity)
        return loaded

    def getWaifuByNameSource(self,name:str,source:str):
        selectedWaifus = [waifu for waifu in self.waifus if waifu.name==name and waifu.source==source]
        try:
            return selectedWaifus[0]
        except IndexError:
            raise WaifuDNEError

    def getWaifuRatings(self):
        return list(map(lambda waifu: waifu.rating,self.waifus))

    def ratingsPlot(self,ax:plt.Axes):
        ax.boxplot(self.getWaifuRatings())
        ax.set_ylabel("Waifu Rating")
        ax.set_title("Waifu Ratings")

    def __repr__(self):
        return f'name:{self.__class__.__name__},guildId={self.identity}\n{len(self.waifus)} waifus={self.waifus}\n{len(self.polls)} polls={self.polls}\noptions={self.options}'

    def addPoll(self,quickLink:str):
        """"
            creates a new poll and starts it, returning the image and view
        """
        if len(self.polls)!=0: #other polls have run
            if self.polls[-1].open: #another poll is running
                raise InvalidPollStateError
        newPoll=Poll(self.identity,self.getOption(ServerOption.PollWaifuCount),quickLink)
        #select options
        (names, sources) = newPoll.startPoll(self.waifus)
        #create image
        image = images.createPollImage(names,sources,self.getOption(ServerOption.PollWaifuImageSizePixels),self.getOption(ServerOption.PollWaifuImageAspect))
        imageBytes=images.imageToBytes(image)
        #create vote buttons
        buttons=newPoll.createPollButtons(len(self.polls))
        self.polls.append(newPoll)
        return (len(self.polls)-1,imageBytes,buttons)

    def endPoll(self):
        if len(self.polls) == 0: #ensure polls have run
            raise InvalidPollStateError
        poll=self.polls[-1]
        if not poll.open: #and that the latest one is open
            raise InvalidPollStateError
        pollResults=poll.endPoll()
        #award points
        for userId in pollResults.awardTickets:
            self.modifyTickets(userId,pollResults.awardTickets[userId])
        #change ratings
        for (name,source) in pollResults.ratingChanges:
            self.getWaifuByNameSource(name,source).updateRating(pollResults.ratingChanges[(name,source)])

    def removePoll(self,poll:Poll):
        self.polls.remove(poll)
    
    def ensureTickets(self,user:int):
        try:
            self.tickets
        except AttributeError:
            self.tickets = dict[int,int]() #backwards compatibility code
        try:
            if user not in self.tickets:
                self.tickets[user]=0
        except TypeError: #account for existing dumb mistake
            self.tickets=dict[int,int]()
            self.tickets[user]=0

    def modifyTickets(self,user:int,delta:int):
        self.ensureTickets(user)
        oldTickets=self.tickets[user]
        if oldTickets + delta < 0:
            raise InsufficientTicketsError
        self.tickets[user] = oldTickets+delta

    def getTickets(self,user:int) -> int:
        self.ensureTickets(user)
        return self.tickets[user]

    def waifuRoll(self,userId:int,tickets:int) -> Waifu:
        if len([waifu for waifu in self.waifus if waifu.claimer == userId]) >= self.getOption(ServerOption.GachaMaxWaifus):
            raise CollectionFullError
        rng=np.random.default_rng()
        #get available waifus and their ratings
        available = [waifu for waifu in self.waifus if waifu.claimer == 0]
        if not available:
            raise InsufficientOptionsError
        ratings=np.array([waifu.rating for waifu in available])
        #generate pick probabilities
        weights=Server.weightsParabolicPiecewise(ratings,tickets,1,3)
        p=weights/np.sum(weights) #as probabilities
        if not np.any(p):
            #can't roll any waifus
            raise UnreachableOptionsError
        try:
            #pick one
            choice = rng.choice(available,1,p=p)[0]
            choice.claim(userId) #mark the waifu claimed
        except ValueError:
            #error means there are no unclaimed left
            raise InsufficientOptionsError
        return choice
    
    @staticmethod
    def weightsBellLike(ratings,tickets:int):
        return np.piecewise(ratings,[ratings<0,ratings>=0],[0,lambda ratings: np.mean(ratings)/((tickets-ratings)**2+1)+np.std(ratings)])

    @staticmethod
    def weightsLinearPiecewise(ratings,tickets,zeroWeight,maxWeight):
        s=np.std(ratings)
        if s<1:
            s=(np.max(ratings)-tickets)/2 #ratings are not very diverse, stretch out
        if s<1:
            s=1 #just to be sure it's not 0 or negative
        m1=(maxWeight-zeroWeight)/tickets
        b1=zeroWeight
        m2=-maxWeight/s
        b2=maxWeight*(tickets+s)/s
        return np.piecewise(ratings,[ratings<0,(0<=ratings)&(ratings<=tickets),(tickets<ratings)&(ratings<=tickets+s),(tickets+s)<ratings],[0,lambda r: m1*r+b1,lambda r: m2*r+b2, 0])


    @staticmethod
    def weightsParabolicPiecewise(ratings,tickets,zeroWeight,maxWeight):
        s=np.std(ratings)
        if s<1:
            s=(np.max(ratings)-tickets)/2 #ratings are not very diverse, stretch out
        if s<1:
            s=1 #just to be sure it's not 0 or negative
        a1=-(maxWeight-zeroWeight)/(tickets*tickets)
        b1=2*(maxWeight-zeroWeight)/tickets
        c1=zeroWeight
        a2=-maxWeight/(s*s)
        b2=2*maxWeight*tickets/(s*s)
        c2=maxWeight-maxWeight*tickets*tickets/(s*s)
        return np.piecewise(ratings,[ratings<0,(0<=ratings)&(ratings<=tickets),(tickets<ratings)&(ratings<=tickets+s),(tickets+s)<ratings],[0,lambda r: a1*r*r+b1*r+c1,lambda r: a2*r*r+b2*r+c2, 0])

    def claimedWaifus(self,userId:int) -> list[Waifu]:
        return [waifu for waifu in self.waifus if waifu.claimer == userId]

    def releaseWaifus(self):
        for waifu in self.waifus:
            if self.timeLeft(waifu) <= 0:
                waifu.release()

    def timeLeft(self,waifu:Waifu):
        if waifu not in self.waifus:
            raise WaifuDNEError
        baseTime = self.getOption(ServerOption.GachaExpiryHours)*sqrt(waifu.level)
        return baseTime - waifu.hoursSinceClaimed