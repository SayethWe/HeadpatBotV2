#python imports
import logging, os
from io import BytesIO
#local imports
import images
from guilds import ServerOption
from polls import Poll
from headpatExceptions import InsufficientOptionsError
from headpatBot import HeadpatBot
#library imports
from disnake import ApplicationCommandInteraction, File, MessageInteraction, Permissions
from disnake.ext import commands
import matplotlib.pyplot as plt

class PollCog(commands.Cog):
    def __init__(self,bot:HeadpatBot):
        self.bot=bot
        self.logger = logging.getLogger(os.environ['LOGGER_NAME'])

    @commands.Cog.listener(name="on_button_click")
    async def pollVoteHandler(self,button_inter:MessageInteraction):
        data = button_inter.component.custom_id.split('|')
        if data[0] != 'poll':
            return
        poll:Poll = self.bot.servers[int(data[1])].polls[int(data[2])]
        if data[3] == 'Confirm':
            outcome=poll.doConfirm(button_inter.author.id)
        else:
            outcome=poll.doVote(button_inter.author.id,int(data[3]))
        
        if outcome==Poll.BUTTON_RESULTS.VOTE_ADD:
            await self.bot.respond(button_inter,'WAIFU.POLL.VOTE.ADD',poll.waifus[int(data[3])].name,ephemeral=True)
        elif outcome==Poll.BUTTON_RESULTS.VOTE_REMOVE:
            await self.bot.respond(button_inter,'WAIFU.POLL.VOTE.REMOVE',poll.waifus[int(data[3])].name,ephemeral=True)
        elif outcome == Poll.BUTTON_RESULTS.CONFIRM:
            await self.bot.respond(button_inter,'WAIFU.POLL.VOTE.CONFIRM',button_inter.author.display_name)
        elif outcome==Poll.BUTTON_RESULTS.CLOSED:
            await self.bot.respond(button_inter,'WAIFU.POLL.VOTE.CLOSED',ephemeral=True)

    @commands.slash_command(
    default_member_permissions=Permissions(manage_messages=True),
    dm_permission=False
    )
    async def poll(
        self,
        inter:ApplicationCommandInteraction
    ):
        pass

    @poll.sub_command(
        description="Start a Waifu Poll"
    )
    async def start(
        self,
        inter:ApplicationCommandInteraction,
        #autoClose:bool = commands.param(True,description="Whether to close this poll automatically based on Server options")
    ):
        await inter.response.defer()
        pollGuild = self.bot.servers[inter.guild.id]
        if len(pollGuild.polls)!=0: #other polls have run
            if pollGuild.polls[-1].open: #another poll is running
                #TODO: include link to message
                await self.bot.respond(inter,'WAIFU.POLL.EXISTS',ephemeral=True)
                return
        quickLink = await inter.original_message()
        quickLink = quickLink.jump_url
        newPoll=Poll(inter.guild.id,pollGuild.getOption(ServerOption.PollWaifuCount),quickLink)
        pollInd=pollGuild.addPoll(newPoll)
        # to run a poll:
        # 1 select options
        try:
            (names, sources) = newPoll.startPoll(pollGuild.waifus)
        except InsufficientOptionsError:
            await self.bot.respond(inter,'WAIFU.POLL.INSUFFICIENT',ephemeral=True)
            pollGuild.removePoll(newPoll)
            return
        # 2 create image
        image = images.createPollImage(names,sources,pollGuild.getOption(ServerOption.PollWaifuImageSizePixels),pollGuild.getOption(ServerOption.PollWaifuImageAspect))
        imageBytes=images.imageToBytes(image)
        attachment = File(imageBytes, filename = 'poll.png')
        # 3 create vote buttons
        buttons=newPoll.createPollButtons(pollInd,names,sources)
        # 4 post image and buttons
        await self.bot.respond(inter,'WAIFU.POLL.OPEN',pollInd,file=attachment,components=buttons)
        # 6 poll end
        #if (autoClose):
        #    delay = pollGuild.getOption(ServerOption.PollParticipationCheckStartHours)
        #    delta=pollGuild.getOption(ServerOption.PollParticipationCheckDeltaHours)
        #    end = pollGuild.getOption(ServerOption.PollEndHours)
        #    threshold = pollGuild.getOption(ServerOption.PollParticipationCheckCount)
        #    pollCog = PollCheckCog(delay,delta,end,newPoll,threshold)
        #    pollCog.checkPoll.start()

    @poll.sub_command(
        description="close a running waifu poll and calculate results"
    )
    async def close(
        self,
        inter:ApplicationCommandInteraction,
    ):
        await inter.response.defer()
        pollGuild = self.bot.servers[inter.guild.id] 
        if len(pollGuild.polls)!=0: #other polls have run
            poll = pollGuild.polls[-1]
        else:
            await self.bot.respond(inter,'WAIFU.POLL.NONE',ephemeral=True)
            return
        if(poll.open):
            pollPoints=poll.endPoll()
            #award points
            for userId in pollPoints:
                pollGuild.modifyTickets(userId,pollPoints[userId])
            #create images
            await self.bot.respond(inter,'WAIFU.POLL.CLOSE')
            await self.results(inter,-1)
        else:
            await self.bot.respond(inter,'WAIFU.POLL.NONE',ephemeral=True)

    @poll.sub_command(
        description="Get results from a poll"
    )
    async def results(
        self,
        inter:ApplicationCommandInteraction,
        poll_num:int = commands.Param(-1,ge=0,description="Which poll to see results for")
    ):
        pollGuild = self.bot.servers[inter.guild.id]
        self.logger.debug(f'Getting results for {inter.guild.id} poll {poll_num}')
        try:
            poll = pollGuild.polls[poll_num]
        except Exception: # wrong index error
            return ##TODO: await
        fig,axs = plt.subplots(2,2,squeeze=False,figsize=(8,8))
        poll.voteHistogram(axs[0,0])
        poll.performancePlot(axs[0,1])
        Poll.ratingCountour(axs[0,1],fig)
        pollGuild.ratingsPlot(axs[1,0])
        poll.resultsTable(axs[1,1])
        fig.suptitle("Waifu poll results")
        fig.set_tight_layout(True)
        figBytes= BytesIO()
        fig.savefig(figBytes)
        plt.close(fig)
        figBytes.seek(0)
        await self.bot.respond(inter,'WAIFU.POLL.RESULTS',file=File(figBytes,filename="results.png"))

    @commands.slash_command(
        description="Get a link to the latest poll"
    )
    async def jump_to_poll(
        self,
        inter:ApplicationCommandInteraction
    ):
        pollGuild = self.bot.servers[inter.guild.id]
        if len(pollGuild.polls)!=0: #other polls have run
            poll = pollGuild.polls[-1]
        else:
            await self.bot.respond(inter,'WAIFU.POLL.JUMP.NONE',ephemeral=True)
            return
        try:
            await self.bot.respond(inter,'WAIFU.POLL.JUMP.SUCCESS',poll.quickLink,ephemeral=True)
        except AttributeError:
            await self.bot.respond(inter,'WAIFU.POLL.JUMP.OLD',ephemeral=True)
        