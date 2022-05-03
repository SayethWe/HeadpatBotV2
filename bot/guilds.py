from enum import Enum
import os, logging
import images
import pickle
from polls import Poll, Waifu
from headpatExceptions import WaifuDNEError,WaifuConflictError
import matplotlib.pyplot as plt

servers=list()

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

    def addWaifu(self,name:str,source:str):
        if os.path.exists(os.path.join(images.POLL_FOLDER,images.sourceNameFolder(name,source))):
            #full database has waifu
            if not self.getWaifuByNameSource(name,source):
                #server does not have waifu
                self.waifus.append(Waifu(name,source,1))
            else:
                raise WaifuConflictError
        else:
            raise WaifuDNEError
    
    def removeWaifu(self,name:str,source:str):
        toRemove=self.getWaifuByNameSource(name,source)
        if not toRemove:
            raise WaifuDNEError
        else:
            self.waifus.remove(toRemove)

    def save(self):
        filePath=os.path.join(SAVE_FOLDER,f'{self.identity}.p')
        with open(filePath,'wb') as saveFile:
            pickle.dump(self,saveFile)

    @staticmethod
    def load(identity:int):
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
            return []

    def getWaifuRatings(self):
        return list(map(lambda waifu: waifu.rating,self.waifus))

    def ratingsPlot(self,ax:plt.Axes):
        ax.violinplot(self.getWaifuRatings())
        ax.set_ylabel("Waifu Rating")
        ax.set_title("Waifu Ratings")

    def __repr__(self):
        return f'name:{self.__class__.__name__},guildId={self.identity}\nwaifus={self.waifus}\npolls={self.polls}\noptions={self.options}'

    def addPoll(self,poll:Poll):
        self.polls.append(poll)

    def removePoll(self,poll:Poll):
        self.polls.remove(poll)