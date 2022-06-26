from __future__ import annotations #allows factory type annotations
from enum import Enum
import os, logging
import images
import pickle
from polls import Poll, Waifu
from headpatExceptions import WaifuDNEError,WaifuConflictError,InsufficientOptionsError
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
        return options
    
    def __init__(self,identity):
        self.identity = identity
        self.waifus=list[Waifu]()
        self.polls=list[Poll]()
        self.options=Server.defaultOptions()
        self.tickets=dict[int,int]

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
        return f'name:{self.__class__.__name__},guildId={self.identity}\nwaifus={self.waifus}\npolls={self.polls}\noptions={self.options}'

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
        if user not in self.tickets:
            self.tickets[user]=0

    def modifyTickets(self,user:int,delta:int):
        self.ensureTickets(user)
        oldTickets=self.tickets[user]
        self.tickets[user] = oldTickets+delta

    def getTickets(self,user:int) -> int:
        self.ensureTickets(user)
        return self.tickets[user]

    def waifuRoll(self,userId:int,tickets:int) -> Waifu:
        rng=np.random.default_rng()
        #get available waifus and their ratings
        available = [waifu for waifu in self.waifus if waifu.claimer == 0 and waifu.rating >= 0]
        ratings=np.array([waifu.rating for waifu in available])
        #generate pick probabilities
        weights=np.mean(ratings)/((tickets-ratings)**2+1)+np.std(ratings)
        p=weights/sum(weights) #as probabilities
        try:
            #pick one
            choice = rng.choice(available,1,p=p)[0]
            choice.claim(userId) #mark the waifu claimed
        except ValueError:
            #error means there are no unclaimed left
            raise InsufficientOptionsError
        return choice

    def claimedWaifus(self,userId:int) -> list[Waifu]:
        return [waifu for waifu in self.waifus if waifu.claimer == userId]