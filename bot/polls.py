import logging, os
from enum import Enum
from datetime import datetime, timezone
import numpy as np
import matplotlib.pyplot  as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from numpy.random import default_rng
from disnake.ui import Button, View
from disnake import ButtonStyle
from disnake.ui import Button
from disnake import ButtonStyle
from headpatExceptions import InsufficientOptionsError

logger = logging.getLogger(os.environ['LOGGER_NAME'])

class Waifu():
    DEFAULT_CLAIM_TIME=datetime(1970,1,1,tzinfo=timezone.utc)

    """
    A server-side Waifu
    """
    def __init__(self,name:str,source:str,rating:int):
        self.name=name
        self.source=source
        self.rating=rating
        self._claimer=0
        self._claimedAt=Waifu.DEFAULT_CLAIM_TIME
        self._level=0

    def __repr__(self):
        return f'{self.name} is a waifu from {self.source} with a rating of {self.rating}'

    def updateRating(self,delta:int):
        self.rating+=delta

    @property
    def claimer(self) -> int|None:
        try:
            self._claimer 
        except AttributeError:
            self._claimer=0 #more backwards compatibility code
        return self._claimer

    @property
    def claimedAt(self) -> datetime:
        try:
            return self._claimedAt
        except AttributeError:
            if self.claimer == 0:
                self._claimedAt=Waifu.DEFAULT_CLAIM_TIME
            else:
                self._claimedAt=datetime.now(timezone.utc)
        return self._claimedAt

    @property
    def hoursSinceClaimed(self) -> float:
        if self.claimedAt==Waifu.DEFAULT_CLAIM_TIME:
            return 0
        else:
            delta = datetime.now(timezone.utc)-self.claimedAt
            return delta.days*24+delta.seconds/3600

    @property
    def level(self) -> int:
        try:
            return self._level
        except AttributeError:
            if self.claimer == 0:
                self._level=1
            else:
                self._level=0
        return self._level

    def claim(self,claimer:int):
        self._claimer=claimer
        self._claimedAt=datetime.now(timezone.utc)
        self._level=1

    def release(self):
        self._claimer=0
        self._claimedAt=Waifu.DEFAULT_CLAIM_TIME
        self._level=0
        #self.updateRating(-1)

    def improve(self):
        self._level+=1

class Poll:
    """
    A single poll object, that handles creation, voting backend, and end calculation
    """
    rng=default_rng()
    VOTING_TICKETS = 2
    MAX_RATING_CHANGE = 8

    class BUTTON_RESULTS(Enum):
        VOTE_ADD=0
        VOTE_REMOVE=1
        CONFIRM=2
        CLOSED=3

    def __init__(self,messageId:int,size:int,quickLink:str):
        self.messageId=messageId
        self.open = False
        self.quickLink = quickLink
        self.users=list[int]()
        self.waifus=list[Waifu]()
        self.ratings=list[int]()
        self.votes=np.zeros(shape=size,dtype=np.int64)
        self.voters=[list[int]() for _ in range(size)]
        self.size = size
        
    def addVote(self,index:int):
        self.votes[index] +=1

    def cancelVote(self,index:int):
        self.votes[index] -=1

    def confirmVotes(self,userId:int):
        self.users.append(userId)

    def getVotes(self):
        return self.votes

    def startPoll(self,waifusIn:list[Waifu]):
        selection = Poll.selectPoll(self.size,[option.rating for option in waifusIn])
        names=list[str]()
        sources=list[str]()
        for index in selection:
            choice = waifusIn[index]
            names.append(choice.name)
            sources.append(choice.source)
            self.ratings.append(choice.rating)
            self.waifus.append(choice)
        self.open=True #only now do we mark open
        return (names,sources)
        
    def endPoll(self): #TODO: maybe take in an inter from commandclose, but if none, do autoclose stuff?
        #TODO: Figure out how to get the original message, and edit it. get_message returned none, and no equivalent fetch seems to exist.
        #fetching a message may actually require the see_messages permissions - is this worth askign for another perm?
        #update waifus
        if not self.users:
            # no one participated
            self.open=False
            logger.debug('Unparticipated poll')
            return {}
        ratingChanges = self.ratingChanges() #determine how much the ratings change
        awardPoints=dict[int,int]()
        #for each waifu in the poll
        for i in range(self.size):
            #remove any users who didn't confirm
            self.voters[i]=set(self.users).intersection(self.voters[i])
            #set total votes to be the length
            self.votes[i]=len(self.voters[i])
            #update the ratings
            self.waifus[i].updateRating(ratingChanges[i])
            #award vote points to waifu claimer
            Poll.addTicketsToDict(awardPoints,self.waifus[i].claimer,Poll.VOTING_TICKETS+int(self.votes[i]*np.log(self.waifus[i].level*self.waifus[i].level+1)))
        #for each user who voted
        for userId in self.users:
            #award participation points
            Poll.addTicketsToDict(awardPoints,userId,Poll.VOTING_TICKETS)
        self.open=False #after everything is done, close the poll, so if we error, it stays open.
        return awardPoints

    @staticmethod
    def addTicketsToDict(ticketsDict:dict[int,int],key:int,amt:int):
        try:
            ticketsDict[key]+=amt
        except KeyError:
            ticketsDict[key]=amt

    def countVotes(self):
        return len(self.users)

    def createPollButtons(self,pollInd:int,names:list[str],sources:list[str]):
        buttons:list[Button]=[None]*(self.size+1)
        for i in range(self.size):
            buttons[i] = Button(style=ButtonStyle.blurple,label=f'{names[i]}|{sources[i]}',custom_id=f'poll|{self.messageId}|{pollInd}|{i}')
        buttons[-1]=Button(style=ButtonStyle.green,label='Confirm',custom_id=f'poll|{self.messageId}|{pollInd}|Confirm')
        return buttons

    def doVote(self,userid:int,voteInd:int):
        if userid in self.users or not self.open: #poll won't take their vote
            return Poll.BUTTON_RESULTS.CLOSED
        elif userid not in self.voters[voteInd]: #user hasn't voted for this - add vote
            self.voters[voteInd].append(userid)
            self.addVote(voteInd)
            return Poll.BUTTON_RESULTS.VOTE_ADD
        else: #user is cancelling a vote
            self.voters[voteInd].remove(userid)
            self.cancelVote(voteInd)
            return Poll.BUTTON_RESULTS.VOTE_REMOVE

    def doConfirm(self,userid:int):
        if userid in self.users or not self.open:
            return Poll.BUTTON_RESULTS.CLOSED
        #TODO lock vote buttons by user, which cannot be done yet.
        self.confirmVotes(userid)
        return Poll.BUTTON_RESULTS.CONFIRM

    def performancePlot(self,ax:plt.Axes):
        expectation=Poll.cubicSigmoid(self.ratings)
        actual=Poll.cubicSigmoid(self.votes)
        ax.plot(expectation,actual,'kX')
        ax.plot([-1,1],[-1,1],'b:')
        ax.set_xlim([-1,1])
        ax.set_xlabel("Expected Performance")
        ax.set_ylim([-1,1])
        ax.set_ylabel("Actual Performance")
        ax.set_aspect('equal')
        ax.set_title("Performance")

    @staticmethod
    def ratingCountour(ax:plt.Axes,fig):
        lin=np.linspace(-1,1,20)
        x,y=np.meshgrid(lin,lin)
        z=Poll.cubicSigmoid(y-x,Poll.MAX_RATING_CHANGE)
        levels=np.arange(-Poll.MAX_RATING_CHANGE,Poll.MAX_RATING_CHANGE+1) #define levels for contours
        cs=ax.contourf(x,y,z,levels,cmap=plt.get_cmap('RdYlGn')) #create the contours, return the contourset
        #create a colorbar
        div=make_axes_locatable(ax)
        cax=div.append_axes('right',size='5%',pad=0.05) #make room for the colorbar
        fig.colorbar(cs,cax=cax,orientation='vertical') #create the bar from the contourset
        
    def voteHistogram(self,ax:plt.Axes):
        ax.hist(self.votes,bins=range(0,len(self.users)+2),align='left')
        ax.set_xlabel("Number of Votes")
        ax.set_ylabel("Occurence Count")
        ax.set_title("Votes by Waifu")
    
    def resultsTable(self,ax:plt.Axes):
        logger.debug(self.votes)
        firstPlace=np.argmax(self.votes)
        worstPlace=np.argmin(self.votes)
        deltaR=self.ratingChanges()
        largestGain=np.argmax(deltaR)
        largestLoss=np.argmin(deltaR)
        results=[
            [self.waifus[firstPlace].name,self.votes[firstPlace]],
            [self.waifus[largestGain].name,deltaR[largestGain]],
            [self.waifus[worstPlace].name,self.votes[worstPlace]],
            [self.waifus[largestLoss].name,deltaR[largestLoss]]]
        logger.debug(results)
        ax.axis('tight')
        t=ax.table(
            cellText=results,
            colLabels=("waifu","value"),
            rowLabels=("First","Gain","Last","Loss"),
            loc='center',
            colWidths=(0.6,0.2)
        )
        t.auto_set_font_size(False)
        t.set_fontsize(12)
        #t.scale(1,2)
        ax.axis('off')
        ax.set_title("Special Mentions")

    def resultsText(self):
        firstPlace=np.argmax(self.votes)
        worstPlace=np.argmax(self.votes)
        dRating=self.ratingChanges()
        largestGain=np.argmax(dRating)
        largestLoss=np.argmin(dRating)
        results=[
            [self.votes[firstPlace],self.waifus[firstPlace].name,self.waifus[firstPlace].source],
            [dRating[largestGain],self.waifus[largestGain].name,self.waifus[largestGain].source],
            [self.votes[worstPlace],self.waifus[worstPlace].name,self.waifus[worstPlace].source],
            [dRating[largestLoss],self.waifus[largestLoss].name,self.waifus[largestLoss].source]]

    @staticmethod
    def selectPoll(pollSize:int,ratings:np.ndarray[int, np.dtype[np.int64]]):
        ratings=np.array(ratings)
        indices=np.argsort(ratings)
        nh = int(np.floor(0.2*pollSize))#number to pick from from top of range...
        nm = int(np.floor(0.3*pollSize))#...middle of range...
        nl = int(np.ceil(0.3*pollSize)) #...bottom of range...
        na = pollSize-(nh+nm+nl)#...and entire range

        if max(nh,nl) >= 0.25*(len(indices)-na): #we're gonna try to pick too many from a quartile
            raise InsufficientOptionsError

        selected=np.zeros(pollSize,dtype=np.int64)
        selected[:na]=Poll.rng.choice(indices,size=na,replace=False)
        indices=np.setdiff1d(indices,selected[:na],assume_unique=True) #remove those uniformly selected from future calculations
        size=len(indices)
        lq=int(0.25*size)
        uq=int(0.75*size)
        selected[na:na+nh]=Poll.rng.choice(indices[uq:],size=nh,replace=False) #from past the upper quartile
        selected[na+nh:na+nh+nm]=Poll.rng.choice(indices[lq:uq],size=nm,replace=False) #the interquartile range
        selected[na+nh+nm:]=Poll.rng.choice(indices[:lq],size=nl,replace=False)#the lowest range
        Poll.rng.shuffle(selected) #shuffle the result so we don't always get consistent placement of similar options
        return selected

    def ratingChanges(self):
        #if self.open:  #ignore for now, as it causes ratings to stagnate with the "only close when logic is done" methodology
            #votes are volatile. return 0
        #    return np.zeros(shape=self.size)
        expectation = Poll.cubicSigmoid(self.ratings)
        actual=Poll.cubicSigmoid(self.votes)
        diff=actual-expectation
        diff=np.append(diff,[-2,2]) #make sure we have the extreme possible values so we don't get different adjustments
        changes=Poll.cubicSigmoid(diff,magnitude=Poll.MAX_RATING_CHANGE)
        changes=changes[:-2] #remove the extremes we added before
        #return np.around(diff*diff*diff)
        return np.around(changes)

    @staticmethod
    def quadraticClamp(data) -> np.ndarray:
        #clamp data. based on f(R_max-R_bar)=1;f(R_min-R_bar)=-1,d/d(R-R_bar)f(R_max-R_bar)=1
        #this means that the maximum distance above the centering metric goes to 1
        #the maximum distance below the centering metric goes to -1
        #and that no value in the rang goes above 1 or below 0
        data=np.array(data)
        X_max=np.max(data)
        X_min=np.min(data)
        X_bar=np.mean(data)
        d=(X_max-X_min)*(X_max-X_min)
        if d != 0:
            a=-2
            b=4*(X_max-X_bar)
            c=(X_min*X_min-2*X_min*X_max-X_max*X_max+4*X_max*X_bar-2*X_bar*X_bar)
            dist = data-X_bar
            return (a*dist*dist+b*dist+c)/d
        else:
            return np.zeros_like(data)
    
    @staticmethod
    def cubicSigmoid(data,magnitude:int=1) -> np.ndarray:
        data=np.array(data)
        X_max=np.max(data)
        X_min=np.min(data)
        denom=(X_max-X_min)*(X_max-X_min)*(X_max-X_min)
        if denom != 0:
            a=-4
            b=6*(X_max+X_min)
            c=-12*X_max*X_min
            d=3*(X_max*X_max*X_min+X_max*X_min*X_min)-X_max*X_max*X_max-X_min*X_min*X_min
            return magnitude*(a*data*data*data+b*data*data+c*data+d)/denom
        else:
            return np.zeros_like(data)

    def __repr__(self) -> str:
        return f'Poll with{vars(self)}'