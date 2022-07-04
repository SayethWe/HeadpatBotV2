from __future__ import annotations #allows factory type annotations
from enum import Enum
import os, logging
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

class Server:
    class ServerOption(Enum):
        PollWaifuCount='pollSize' #how many waifus to put in a poll
        PollParticipationCheckStartHours='pollCheckZero' #when to start checking for poll participations
        PollParticipationCheckDeltaHours='pollCheckDelta' #how often to check poll participation
        PollEndHours='pollForceEnd' #when to stop checkign and just end the poll
        PollParticipationCheckCount='pollParticipation' #how many people should vote to end poll
        PollWaifuImageSizePixels='waifuImageSize' #how many pixels to make the tiles in the poll collage, unused
        PollStartNextGapHours='pollNextDelay' #how long to wait after endeing a poll to start the next, unused
        GachaMaxWaifus='gachaMaximumCollection'

    @staticmethod
    def defaultOptions():
        options=dict[str,int]()
        options[Server.ServerOption.PollWaifuCount.value]=8
        options[Server.ServerOption.PollParticipationCheckStartHours.value]=36
        options[Server.ServerOption.PollParticipationCheckDeltaHours.value]=2
        options[Server.ServerOption.PollEndHours.value]=48
        options[Server.ServerOption.PollParticipationCheckCount.value]=6
        options[Server.ServerOption.PollWaifuImageSizePixels.value]=500
        options[Server.ServerOption.PollStartNextGapHours.value] = 24
        options[Server.ServerOption.GachaMaxWaifus.value] = 8
        return options
    
    def __init__(self,identity):
        self.identity = identity
        self.waifus=list[Waifu]()
        self.polls=list[Poll]()
        self.options=Server.defaultOptions()
        self.tickets=dict[int,int]()

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
            pickle.dump(self,saveFile)

    def delete(self):
        filePath=os.path.join(SAVE_FOLDER,f'{self.identity}.p')
        os.remove(filePath)

    @staticmethod
    def load(identity:int) -> Server:
        try:
            with open(os.path.join(SAVE_FOLDER,f'{identity}.p'),'rb') as loadFile:
                loaded = pickle.load(loadFile)
            for option in Server.ServerOption:
                try:
                    loaded.options[option.value]
                except(AttributeError):
                    #options do not exist
                    logger.info(f'{loaded.identity} did not have options. Creating defaults')
                    loaded.options=Server.defaultOptions()
                except(KeyError):
                    #option not in existence
                    logger.info(f'{loaded.identity} was missing a value for {option}. Setting to default.')
                    loaded.options[option.value]=Server.defaultOptions()[option.value]
            return loaded
        except FileNotFoundError:
            return Server(identity)

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

    def addPoll(self,poll:Poll):
        self.polls.append(poll)
        return len(self.polls)-1

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
        if len([waifu for waifu in self.waifus if waifu.claimer == userId]) >= self.options[Server.ServerOption.GachaMaxWaifus.value]:
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