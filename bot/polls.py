import logging, os
from re import A
import numpy as np
import matplotlib.pyplot  as plt
from numpy.random import default_rng
from disnake.ui import Button, View
from disnake import ButtonStyle
from disnake.ui import Button
from disnake import ButtonStyle, MessageInteraction
from disnake.ext.commands import Bot
from headpatExceptions import InsufficientOptionsError
import responder

logger = logging.getLogger(os.environ['LOGGER_NAME'])

class Waifu():
    """
    A server-side Waifu
    """
    def __init__(self,name:str,source:str,rating:int):
        self.name=name
        self.source=source
        self.rating=rating

    def __repr__(self):
        return f'{self.name} is a waifu from {self.source} with a rating of {self.rating}'

    def updateRating(self,delta:int):
        self.rating+=delta

class Poll():
    """
    A single poll object, that handles creation, voting backend, and end calculation
    """
    rng=default_rng()

    def __init__(self,messageId:int,size:int):
        self.messageId=messageId
        self.open = True
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
        return (names,sources)
        
    def endPoll(self,bot:Bot): #TODO: maybe take in an inter from commandclose, but if none, do autoclose stuff?
        self.open=False
        #TODO: Figure out how to get the original message, and edit it. get_message returned none, and no equivalent fetch seems to exist.
        #fetching a message may actually require the see_messages permissions - is this worth askign for another perm?
        #update waifus
        if not self.users:
            # no one participated
            return
        #for each list in voters
        for i in range(self.size):
            #remove any users who didn't confirm
            self.voters[i]=set(self.users).intersection(self.voters[i])
            #set votes to be the length
            self.votes[i]=len(self.voters[i])
        ratingChanges = self.ratingChanges()
        for i in range(self.size):
            self.waifus[i].updateRating(ratingChanges[i])

    def countVotes(self):
        return len(self.users)

    def createPollView(self, names:list[str],sources:list[str]):
        view = View(timeout=None)
        for i in range(len(names)):
            button = VoteButton(names[i],sources[i],i,self)
            view.add_item(button)
        view.add_item(ConfirmButton(self))
        return view

    def createPollButtons(self,pollInd:int,names:list[str],sources:list[str]):
        buttons:list[Button]=[None]*(self.size+1)
        for i in range(self.size):
            buttons[i] = Button(style=ButtonStyle.blurple,label=f'{names[i]}|{sources[i]}',custom_id=f'poll|{self.messageId}|{pollInd}|{i}')
        buttons[-1]=Button(style=ButtonStyle.green,label='Confirm',custom_id=f'poll|{self.messageId}|{pollInd}|Confirm')
        return buttons

    async def doVote(self,button_inter:MessageInteraction,voteInd:int):
        user=button_inter.author.id
        if user in self.users or not self.open: #poll won't take their vote
            await button_inter.send(responder.getResponse('WAIFU.POLL.VOTE.CLOSED'),ephemeral=True)
        elif user not in self.voters[voteInd]: #user hasn't voted for this - add vote
            await button_inter.send(responder.getResponse('WAIFU.POLL.VOTE.ADD',self.waifus[voteInd].name),ephemeral=True)
            self.voters[voteInd].append(user)
            self.addVote(voteInd)
        else: #user is cancelling a vote
            await button_inter.send(responder.getResponse('WAIFU.POLL.VOTE.REMOVE',self.waifus[voteInd].name),ephemeral=True)
            self.voters[voteInd].remove(user)
            self.cancelVote(voteInd)

    async def doConfirm(self,button_inter:MessageInteraction):
        user=button_inter.author
        if user in self.users or not self.open:
            await button_inter.send(responder.getResponse('WAIFU.POLL.VOTE.CLOSED'),ephemeral=True)
            return
        #TODO lock vote buttons by user, which cannot be done yet.
        self.confirmVotes(user.id)
        try:
            name = user.nick
            assert name is not None
        except:
            name = user.name
        await button_inter.send(responder.getResponse('WAIFU.POLL.VOTE.CONFIRM',name))

    def performancePlot(self,ax:plt.Axes):
        expectation=Poll.cubicSigmoid(self.ratings)
        actual=Poll.cubicSigmoid(self.votes)
        ax.plot(expectation,actual,'r*')
        ax.plot([-1,1],[-1,1],'b:')
        ax.set_xlim([-1,1])
        ax.set_xlabel("Expected Performance")
        ax.set_ylim([-1,1])
        ax.set_ylabel("Actual Performance")
        ax.set_aspect('equal')
        ax.set_title("Performance")

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

        if max(nh,nl) >= 0.25*(len(indices)-na): #we're gonna have a problem
            raise InsufficientOptionsError

        selected=np.zeros(pollSize,dtype=np.int64)
        selected[:na]=Poll.rng.choice(indices,size=na,replace=False)
        indices=np.setdiff1d(indices,selected[:na],assume_unique=True)
        size=len(indices)
        lq=int(0.25*size)
        uq=int(0.75*size)
        selected[na:na+nh]=Poll.rng.choice(indices[uq:],size=nh,replace=False) #from past the upper quartile
        selected[na+nh:na+nh+nm]=Poll.rng.choice(indices[lq:uq],size=nm,replace=False) #the interquartile range
        selected[na+nh+nm:]=Poll.rng.choice(indices[:lq],size=nl,replace=False)#the lowest range
        Poll.rng.shuffle(selected) #shuffle the result so we don't always get consistent placement of similar options
        return selected

    def ratingChanges(self):
        if self.open:
            #votes are volatile. return 0
            return np.zeros(shape=self.size)
        expectation = Poll.cubicSigmoid(self.ratings)
        actual=Poll.cubicSigmoid(self.votes)
        diff=actual-expectation
        return np.around(diff*diff*diff)

    @staticmethod
    def quadraticClamp(data):
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
    def cubicSigmoid(data):
        data=np.array(data)
        X_max=np.max(data)
        X_min=np.min(data)
        denom=(X_max-X_min)*(X_max-X_min)*(X_max-X_min)
        if denom != 0:
            a=-4
            b=6*(X_max+X_min)
            c=-12*X_max*X_min
            d=3*(X_max*X_max*X_min+X_max*X_min*X_min)-X_max*X_max*X_max-X_min*X_min*X_min
            return (a*data*data*data+b*data*data+c*data+d)/denom
        else:
            return np.zeros_like(data)

class VoteButton(Button):
    def __init__(self, name:str, source:str,index:int,poll:Poll):
        self.selected = False
        self.name=name
        self.poll=poll
        self.index=index
        self.users=list[int]()
        super().__init__(style=ButtonStyle.blurple,label=f'{name}|{source}')

    async def callback(self, button_inter : MessageInteraction):
        user=button_inter.author.id
        if user in self.poll.users or not self.poll.open:
            await button_inter.send(responder.getResponse('WAIFU.POLL.VOTE.CLOSED'),ephemeral=True)
        elif user not in self.users:
            await button_inter.send(responder.getResponse('WAIFU.POLL.VOTE.ADD',self.name),ephemeral=True)
            self.users.append(user)
            self.poll.addVote(self.index)
        else:
            await button_inter.send(responder.getResponse('WAIFU.POLL.VOTE.REMOVE',self.name),ephemeral=True)
            self.users.remove(user)
            self.poll.cancelVote(self.index)

class ConfirmButton(Button):

    def __init__(self,poll:Poll):
        self.poll=poll
        super().__init__(style=ButtonStyle.green,label='confirm')

    async def callback(self, button_inter: MessageInteraction):
        user=button_inter.author
        if user in self.poll.users or not self.poll.open:
            await button_inter.send(responder.getResponse('WAIFU.POLL.VOTE.CLOSED'),ephemeral=True)
            return
        #TODO lock vote buttons by user, which cannot be done yet.
        self.poll.confirmVotes(user.id)
        await button_inter.send(responder.getResponse('WAIFU.POLL.VOTE.CONFIRM',user.name))