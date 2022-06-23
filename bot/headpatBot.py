import os, sys, logging
os.environ['LOGGER_NAME']='disnake'

logger = logging.getLogger(os.environ['LOGGER_NAME'])
logger.setLevel(logging.DEBUG)
format=logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

fhandler = logging.FileHandler(filename='discord.log', encoding = 'utf-8', mode = 'w')
fhandler.setLevel('DEBUG')
fhandler.setFormatter(format)
logger.addHandler(fhandler)

chandler = logging.StreamHandler(stream = sys.stdout)
chandler.setFormatter(format)
chandler.setLevel('INFO')
logger.addHandler(chandler)

import asyncio
from dataclasses import dataclass
from pickle import UnpicklingError
import disnake
from disnake import ApplicationCommandInteraction, File
from disnake.ext import tasks, commands
import images, responder, guilds, polls, approval, database, headpatExceptions
import glob
import matplotlib.pyplot  as plt
from io import BytesIO
import traceback

TOKEN=os.environ['DISCORD_TOKEN']
intents = disnake.Intents(guilds=True)

if 'TEST_ENV' in os.environ:
    bot=commands.Bot(
        intents=intents,
        test_guilds=[741829543718944768],
        help_command=commands.DefaultHelpCommand()
    )
else:
     bot=commands.Bot(
        intents=intents,
        help_command=commands.DefaultHelpCommand()
    )

servers=dict[int,guilds.Server]()

# Helpers
async def source_autocomplete(
    inter:ApplicationCommandInteraction,
    input:str
):
    raw_list = glob.glob('*/*/',root_dir=images.POLL_FOLDER)
    valid = sorted(set([source.split('/')[0] for source in raw_list if input.title() in source]))
    return valid[:25] #discord can take 25 options

async def name_autocomplete(
    inter:ApplicationCommandInteraction,
    input:str
):
    raw_list = glob.glob('*/*/',root_dir=images.POLL_FOLDER)
    valid = sorted(set([source.split('/')[1] for source in raw_list if input.title() in source]))
    return valid[:25]

@dataclass
class WaifuData:
    name:str
    source: str

@commands.register_injection
async def getWaifu(
    inter:ApplicationCommandInteraction,
    name:str=commands.Param(autocomplete=name_autocomplete,description="Name of waifu"),
    source:str=commands.Param(autocomplete=source_autocomplete,description="Origin of Waifu")
) -> WaifuData:
    return WaifuData(name.title(),source.title())

# Events
@bot.event
async def on_ready(): #events to fire on a sucessful reconnection
    logger.info(f"Logging in as {bot.user}")
    for guild in bot.guilds:
        try:
            servers[guild.id] = await database.getGuildPickle(guild.id)
        except (UnpicklingError, TypeError):
            servers[guild.id]=guilds.Server.load(guild.id)
        logger.info(f"loading server {guild.name} with id {guild.id}")
    logger.info('bot is ready')

@bot.event
async def on_disconnect(): #events to fire when closing
    storageCog = bot.get_cog('StorageCog')
    await storageCog.storeFiles()
    await storageCog.storeDatabase()

@bot.event
async def on_slash_command_error(
    inter:ApplicationCommandInteraction,
    err:commands.CommandError
):
    try:
        logger.error(f'Slash Command Error from {inter.guild.name}|{inter.channel.name}: {err}')
        logger.error(traceback.format_exc(err))
        if isinstance(err,commands.CheckFailure): #should never run now, but keep in just in case.
            await inter.send(responder.getResponse('ERROR.NOT_PERMITTED'),ephemeral=True)
        elif isinstance(err,commands.MissingRequiredArgument):
            await inter.send(responder.getResponse('ERROR.ARGUMENT'),ephemeral=True)
        else:
            await inter.send(responder.getResponse('ERROR.GENERIC'),ephemeral=True)
    except Exception as err2:
        #last ditch effort to get some info to the log and user
        logger.critical(err)
        logger.critical(traceback.format_exc(err))
        logger.critical(f'an error occured while handling previous error: {err2}')

### help command TODO
@bot.slash_command(
    description="Get command and bot documentation"
)
async def help(
    inter: ApplicationCommandInteraction
):
    await inter.send(responder.getResponse('HELP'),file=File("README.md"),ephemeral=True)

# slash commands
@bot.slash_command(
    description = "get headpats, up to four at a time."
)
async def headpat(
    inter:ApplicationCommandInteraction,
    qty:int=commands.Param(default=1,le=4,gt=0)
):
    for i in range(max(1,min(qty,4))):
        image=images.loadHeadpatImage()
        imageBytes=images.imageToBytes(image)
        attachment = File(imageBytes, filename = 'headpat.png')
        await inter.send(responder.getResponse('HEADPAT.PASS'),file=attachment)

## Option Commands
@bot.slash_command(
    description="set server options"
)
async def options(
    inter:ApplicationCommandInteraction,
    setting:guilds.Server.ServerOption=commands.Param(description="option to set"),
    setValue:int= commands.Param(default=-1,ge=0,description="value to set option to")
):
    guild=servers[inter.guild.id]
    if setValue == -1:
        #show value
        await inter.send(responder.getResponse('OPTION.GET',setting,guild.options[setting]))
    else:
        #set value
        guild.options[setting]=setValue
        await inter.send(responder.getResponse('OPTION.SET',setting,setValue))

## Waifu Commands
@bot.slash_command()
async def waifu(inter:ApplicationCommandInteraction):
    pass

@waifu.sub_command(
    description="Suggest a waifu and/or image for inclusion in the bot"
)
async def suggest(
    inter:ApplicationCommandInteraction,
    image:disnake.Attachment, 
    waifuData:WaifuData
):
    if image.content_type.startswith('image'):
        name=waifuData.name
        source=waifuData.source
        await inter.send(responder.getResponse('WAIFU.ADD.WAIT'))
        await approval.getWaifuApproval(bot,image,name,source)
    else:
        await inter.send(responder.getResponse('WAIFU.ADD.NOT_IMAGE'))

@waifu.sub_command(
    description="Show an image of a waifu from the global database"
)
async def show(
    inter:ApplicationCommandInteraction,
    waifuData:WaifuData
):
    name=waifuData.name
    source=waifuData.source
    image = images.loadPollImage(os.path.join(source,name))
    imageBytes = images.imageToBytes(image,name)
    attachment = File(imageBytes, filename = f'{name}.png')
    reply = responder.getResponse('WAIFU.SHOW.PASS')
    await inter.send(reply,file=attachment)

@waifu.sub_command(
    description="get a list of waifus, either in this server, or available for pulls"
)
async def getList(
    inter:ApplicationCommandInteraction,
    scope:str=commands.Param(
        choices=["Local","Global","NotInServer"],
        description="Whether to consider only this server (Local) or the master database (Global)"
    )
):
    reply = ""
    with open('Waifus.txt','w') as waifuList:
        await inter.response.defer()
        if scope == "Global":
            count=0
            for waifuStr in glob.glob('*/*/',root_dir=images.POLL_FOLDER):
                (source,name,*discard) = waifuStr.split('/')
                waifuList.write(f'{name} from {source}\n')
                count+=1
            reply = responder.getResponse('WAIFU.LIST.GLOBAL',count)
        elif scope == 'Local':
            waifus=servers[inter.guild.id].waifus
            reply = responder.getResponse('WAIFU.LIST.LOCAL',len(waifus))
            for waifu in waifus:
                waifuList.write(f"{waifu}\n")
        else:
            count=0
            for waifuStr in glob.glob('*/*/',root_dir=images.POLL_FOLDER):
                (source,name,*discard) = waifuStr.split('/')
                if not servers[inter.guild.id].getWaifuByNameSource(name,source):
                    waifuList.write(f'{name} from {source}\n')
                    count+=1
            reply = responder.getResponse('WAIFU.LIST.DIFFERENCE',count)
    with open('Waifus.txt','rb') as waifuList:
        file = disnake.File(waifuList, filename='Waifus.txt')
        await inter.send(reply,file=file,ephemeral=True)

@bot.slash_command()
async def manageWaifus(inter:ApplicationCommandInteraction):
    pass

@manageWaifus.sub_command(
    description = "add a waifu to future polls on this server"
)
async def pull(
    inter:ApplicationCommandInteraction,
    waifuData:WaifuData
):
    name=waifuData.name
    source=waifuData.source
    try:
        servers[inter.guild.id].addWaifu(name,source)
        reply=responder.getResponse('WAIFU.PULL.PASS',name,source)
    except headpatExceptions.WaifuConflictError:
        reply=responder.getResponse('WAIFU.ERROR.CONFLICT',name,source)
    except headpatExceptions.WaifuDNEError:
        reply=responder.getResponse('WAIFU.ERROR.DNE',name,source)
    await inter.send(reply)

@manageWaifus.sub_command(
    description="remove a waifu from further polls on this server"
)
async def remove(
    inter:ApplicationCommandInteraction,
    waifuData:WaifuData
):
    name=waifuData.name
    source=waifuData.source
    try:
        servers[inter.guild.id].removeWaifu(name,source)
        reply=responder.getResponse('WAIFU.REMOVE.PASS',name,source)
    except headpatExceptions.WaifuDNEError:
        reply=responder.getResponse('WAIFU.ERROR.DNE',name,source)
    await inter.send(reply)

@manageWaifus.sub_command(
    description="add a whole list of waifus defined in a CSV to your server"
)
async def pullCSV(
    inter:ApplicationCommandInteraction,
    csv:disnake.Attachment, 
):
    await inter.response.defer()
    if csv.content_type.startswith('text/csv'):
        waifus=await csv.read()
        waifus = waifus.decode()
        waifus = waifus.split('\n')
        with open(f"failedList{inter.guild.id}.txt",'w') as failedList:
            failedList.write("Failed Waifus:\n")
            numFailed=0
            for waifu in waifus:
                logger.debug(waifu)
                waifu=waifu.replace('\r','').replace('\n','')
                info=waifu.split(',')
                try:
                    servers[inter.guild.id].addWaifu(info[0],info[1])
                except headpatExceptions.WaifuDNEError:
                    numFailed+=1
                    failedList.write(f'unable to find in database: {waifu}\n')
                except headpatExceptions.WaifuConflictError:
                    numFailed+=1
                    failedList.write(f'already present in server:  {waifu}\n')

        if(numFailed>0):
            with open(f"failedList{inter.guild.id}.txt",'rb') as failedList:
                file = disnake.File(failedList,filename="Failed Waifus.txt")
                await inter.send(responder.getResponse('WAIFU.PULL.CSV.PASS', len(waifus)-numFailed),file=file,ephemeral=True)
        else:
            await inter.send(responder.getResponse('WAIFU.PULL.CSV.PASS', len(waifus)))
    else:
        await inter.send(responder.getResponse('WAIFU.PULL.CSV.NOT_CSV'),ephemeral=True)


### Poll Commands
@bot.slash_command()
async def poll(inter:ApplicationCommandInteraction):
    pass

@poll.sub_command(
    description="Start a Waifu Poll"
)
async def start(
    inter:ApplicationCommandInteraction,
    #autoClose:bool = commands.param(True,description="Whether to close this poll automatically based on Server options")
):
    await inter.response.defer()
    pollGuild = servers[inter.guild.id]
    if len(pollGuild.polls)!=0: #other polls have run
        if pollGuild.polls[-1].open: #another poll is running
            #TODO: include link to message
            await inter.send(responder.getResponse('WAIFU.POLL.EXISTS'),ephemeral=True)
            return
    newPoll=polls.Poll(inter.channel_id,pollGuild.options[guilds.Server.ServerOption.PollWaifuCount.value])
    pollGuild.addPoll(newPoll)
    # to run a poll:
    # 1 select options
    try:
        (names, sources) = newPoll.startPoll(pollGuild.waifus)
    except headpatExceptions.InsufficientOptionsError:
        await inter.send(responder.getResponse('WAIFU.POLL.INSUFFICIENT'),ephemeral=True)
        pollGuild.removePoll(newPoll)
        return
    # 2 create image
    image = images.createPollImage(names,sources)
    imageBytes=images.imageToBytes(image)
    attachment = File(imageBytes, filename = 'poll.png')
    # 3 create vote buttons
    view = newPoll.createPollView(names,sources)
    # 4 post image and buttons
    reply = responder.getResponse('WAIFU.POLL.OPEN')
    await inter.send(content=reply,file=attachment,view=view)
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
    inter:ApplicationCommandInteraction,
):
    await inter.response.defer()
    pollGuild = servers[inter.guild.id] 
    if len(pollGuild.polls)!=0: #other polls have run
        poll = pollGuild.polls[-1]
    else:
        await inter.send(responder.getResponse('WAIFU.POLL.NONE'),ephemeral=True)
        return
    if(poll.open):
        poll.endPoll(bot)
        #create images
        await inter.send(responder.getResponse('WAIFU.POLL.CLOSE') )
        await results(inter,-1)
    else:
        await inter.send(responder.getResponse('WAIFU.POLL.NONE'),ephemeral=True)

@poll.sub_command(
    description="Get results from a poll"
)
async def results(
    inter:ApplicationCommandInteraction,
    pollNum:int = commands.Param(-1,le=0,description="Which poll to see results for")
):
    pollGuild = servers[inter.guild.id]
    logger.debug(f'Getting results for {inter.guild.id} poll {pollNum}')
    try:
        poll = pollGuild.polls[pollNum]
    except Exception: # wrong index error
        return ##TODO: await
    fig,axs = plt.subplots(1,3,squeeze=False)
    poll.voteHistogram(axs[0,0])
    poll.performancePlot(axs[0,1])
    pollGuild.ratingsPlot(axs[0,2])
    fig.suptitle("Waifu poll results")
    fig.set_tight_layout(True)
    figBytes= BytesIO()
    fig.savefig(figBytes)
    plt.close(fig)
    figBytes.seek(0)
    await inter.send(responder.getResponse('WAIFU.POLL.RESULTS'),file=File(figBytes,filename="results.png"))

class PollCheck:
    def __init__(self,delay:int,delta:int,end:int,poll:polls.Poll,threshold:int):
        self.delay=delay
        self.delta=delta
        self.end=end
        self.count = int((end-delay)/delta)+1
        self.poll=poll
        self.threshold = threshold
        self.checkPoll.change_interval(hours=delta)

    @tasks.loop(hours=2)
    async def checkPoll(self):
        if self.poll.countVotes() >= self.threshold or self.checkPoll.current_loop >= self.count:
            self.checkPoll.stop()

    @checkPoll.before_loop
    async def pollWait(self):
        await asyncio.sleep(self.delay*3600)

    @checkPoll.after_loop
    async def endPoll(self):
        #end the poll
        if self.poll.open:
            self.poll.endPoll(bot)


class StorageCog(commands.Cog):
    def __init__(self,bot:commands.Bot):
        self.bot=bot
        self.loadFiles.start()
        self.storeFiles.start()
        self.storeDatabase.start()

    @tasks.loop(hours=4)
    async def storeFiles(self):
        logger.info('Saving Files')
        for server in servers.values():
            server.save()

    @tasks.loop(hours=2)
    @storeFiles.after_loop
    async def storeDatabase(self):
        logger.info('Saving filesystem to database')
        for server in servers.values():
            await database.storeGuildPickle(server)
        for waifuImage in glob.glob('*/*/*.qoi',root_dir=images.POLL_FOLDER):
            waifuData=waifuImage.split('/')
            imagePath=os.path.join(images.POLL_FOLDER,waifuImage)
            await database.storeWaifuFile(waifuData[1],waifuData[0],imagePath,int(waifuData[2].replace('.qoi','')))

    @storeDatabase.before_loop
    @storeFiles.before_loop
    async def waitForLoaded(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=6)
    async def loadFiles(self):
        logger.info('Fetching from Database to File System')
        allWaifus=await database.getAllWaifus()
        for waifu in allWaifus:
            name=waifu[0]
            source=waifu[1]
            waifuHashes = await database.getWaifuHashes(name,source)
            for waifuHash in waifuHashes:
                waifuImage=await database.loadWaifu(waifuHash)
                images.saveRawPollImage(waifuImage,waifuHash,images.sourceNameFolder(name,source))
        allGuilds=await database.getAllGuilds()
        for guildId in allGuilds:
            guild = await database.getGuildPickle(guildId)
            guild.save()

bot.add_cog(StorageCog(bot))
bot.run(TOKEN)