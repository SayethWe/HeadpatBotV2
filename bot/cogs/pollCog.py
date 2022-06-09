import logging, os, asyncio
import images, responder
from guilds import Server
from polls import Poll
from headpatExceptions import InsufficientOptionsError
from disnake import ApplicationCommandInteraction, File
from disnake.ext import commands
import disnake
import matplotlib.pyplot as plt
from io import BytesIO

class PollCog(commands.Cog):
    def __init__(self,bot:commands.Bot):
        self.bot=bot
        self.logger = logging.getLogger(os.environ['LOGGER_NAME'])

    @commands.Cog.listener(name="on_button_click")
    async def pollVoteHandler(self,inter:disnake.MessageInteraction):
        data = inter.component.custom_id.split('|')
        if data[0] != 'poll':
            return
        poll:Poll = self.bot.servers[int(data[1])].polls[int(data[2])]
        if data[3] == 'Confirm':
            await poll.doConfirm(inter)
        else:
            await poll.doVote(inter,int(data[3]))

    @commands.slash_command(
    default_permission=disnake.Permissions(manage_messages=True),
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
                await inter.send(responder.getResponse('WAIFU.POLL.EXISTS'),ephemeral=True)
                return
        newPoll=Poll(inter.guild.id,pollGuild.options[Server.ServerOption.PollWaifuCount.value])
        pollInd=pollGuild.addPoll(newPoll)
        # to run a poll:
        # 1 select options
        try:
            (names, sources) = newPoll.startPoll(pollGuild.waifus)
        except InsufficientOptionsError:
            await inter.send(responder.getResponse('WAIFU.POLL.INSUFFICIENT'),ephemeral=True)
            pollGuild.removePoll(newPoll)
            return
        # 2 create image
        image = images.createPollImage(names,sources)
        imageBytes=images.imageToBytes(image)
        attachment = File(imageBytes, filename = 'poll.png')
        # 3 create vote buttons
        buttons=newPoll.createPollButtons(pollInd,names,sources)
        # 4 post image and buttons
        reply = responder.getResponse('WAIFU.POLL.OPEN')
        await inter.send(content=reply,file=attachment,components=buttons)
        # 6 poll end
        #if (autoClose):
        #    delay = pollGuild.options[guilds.Server.ServerOption.PollParticipationCheckStartHours.value]
        #    delta=pollGuild.options[guilds.Server.ServerOption.PollParticipationCheckDeltaHours.value]
        #    end = pollGuild.options[guilds.Server.ServerOption.PollEndHours.value]
        #    threshold = pollGuild.options[guilds.Server.ServerOption.PollParticipationCheckCount.value]
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
            await inter.send(responder.getResponse('WAIFU.POLL.NONE'),ephemeral=True)
            return
        if(poll.open):
            poll.endPoll(self.bot)
            #create images
            await inter.send(responder.getResponse('WAIFU.POLL.CLOSE') )
            await self.results(inter,-1)
        else:
            await inter.send(responder.getResponse('WAIFU.POLL.NONE'),ephemeral=True)

    @poll.sub_command(
        description="Get results from a poll"
    )
    async def results(
        self,
        inter:ApplicationCommandInteraction,
        pollNum:int = commands.Param(-1,ge=0,description="Which poll to see results for")
    ):
        pollGuild = self.bot.servers[inter.guild.id]
        self.logger.debug(f'Getting results for {inter.guild.id} poll {pollNum}')
        try:
            poll = pollGuild.polls[pollNum]
        except Exception: # wrong index error
            return ##TODO: await
        fig,axs = plt.subplots(2,2,squeeze=False,figsize=(8,8))
        poll.voteHistogram(axs[0,0])
        poll.performancePlot(axs[0,1])
        pollGuild.ratingsPlot(axs[1,0])
        poll.resultsTable(axs[1,1])
        fig.suptitle("Waifu poll results")
        fig.set_tight_layout(True)
        figBytes= BytesIO()
        fig.savefig(figBytes)
        plt.close(fig)
        figBytes.seek(0)
        await inter.send(responder.getResponse('WAIFU.POLL.RESULTS'),file=File(figBytes,filename="results.png"))