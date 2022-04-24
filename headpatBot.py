import os, sys, logging
os.environ['LOGGER_NAME']='discord'

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

TOKEN=os.environ['DISCORD_TOKEN']

intents = disnake.Intents.none()

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
    valid = sorted([source.split('/')[0] for source in raw_list if input.title() in source])
    return valid[:25] #discord can take 25 options

async def name_autocomplete(
    inter:ApplicationCommandInteraction,
    input:str
):
    raw_list = glob.glob('*/*/',root_dir=images.POLL_FOLDER)
    valid = sorted([source.split('/')[1] for source in raw_list if input.title() in source])
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
    storageCog = bot.get_cog('StorageCog')
    for guild in bot.guilds:
        try:
            servers[guild.id] = database.getGuildPickle(guild.id)
        except (UnpicklingError, TypeError):
            servers[guild.id]=guilds.Server.load(guild.id)
        logger.info(f"loading server {guild.name} with id {guild.id}")
    #also need to make sure waifus are in system from database

@bot.event
async def on_disconnect(): #events to fire when closing
    storageCog = bot.get_cog('StorageCog')
    storageCog.storeFiles()
    storageCog.storeDatabase()

@bot.event
async def on_slash_command_error(
    inter:ApplicationCommandInteraction,
    err:commands.CommandError
):
    logger.error(f'Slash Command Error from {inter.guild.name}|{inter.channel.name}: {err}')
    if isinstance(err,commands.CheckFailure):
        await inter.send(responder.getResponse('ERROR.NOT_PERMITTED'),ephemeral=True)
    elif isinstance(err,commands.MissingRequiredArgument):
        await inter.send(responder.getResponse('ERROR.ARGUMENT'),ephemeral=True)
    else:
        await inter.send(responder.getResponse('ERROR.GENERIC'),ephemeral=True)

# Checks
def is_not_me(inter:ApplicationCommandInteraction):
    return inter.author.id != 132650983011385347

### help command TODO

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
@commands.check(commands.has_guild_permissions(administrator=True))
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
@commands.check(commands.has_permissions(attach_files=True))
async def getList(
    inter:ApplicationCommandInteraction,
    scope:str=commands.Param(
        choices=["Local","Global"],
        description="Whether to consider only this server (Local) or the master database (Global)"
    )
):
    reply = ""
    with open('Waifus.txt','w') as waifuList:
        if scope == "Global":
            reply = responder.getResponse('WAIFU.LIST.GLOBAL')
            for waifuStr in glob.glob('*/*/',root_dir=images.POLL_FOLDER):
                waifuData = waifuStr.split('/')
                waifuList.write(f'{waifuData[1]} from {waifuData[0]}\n')
        else:
            waifus=servers[inter.guild.id].waifus
            reply = responder.getResponse('WAIFU.LIST.LOCAL',len(waifus))
            for waifu in waifus:
                waifuList.write(f"{waifu}\n")
    with open('Waifus.txt','rb') as waifuList:
        file = disnake.File(waifuList, filename='Waifus.txt')
        await inter.send(reply,file=file,ephemeral=True)
    
@waifu.sub_command(
    description = "add a waifu to future polls on this server"
)
@commands.check(commands.has_guild_permissions(manage_messages=True))
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

@waifu.sub_command(
    description="remove a waifu from further polls on this server"
)
@commands.check(commands.has_guild_permissions(manage_messages=True))
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

@waifu.sub_command(
    description="add a whole list of waifus defined in a CSV to your server"
)
@commands.check(commands.has_guild_permissions(manage_messages=True))
async def pullCSV(
    inter:ApplicationCommandInteraction,
    csv:disnake.Attachment, 
):
    if csv.content_type.startswith('text/csv'):
        waifus=await csv.read()
        waifus = waifus.decode()
        waifus = waifus.split('\n')
        for waifu in waifus:
            info=waifu.split(',')
            servers[inter.guild.id].addWaifu(info[0],info[1])
        await inter.send(responder.getResponse('WAIFU.PULL.CSV.PASS', len(waifus)))
    else:
        await inter.send(responder.getResponse('WAIFU.PULL.CSV.NOT_CSV'))


### Poll Commands
@waifu.sub_command_group()
@commands.check(commands.has_guild_permissions(administrator=True))
async def poll(inter:ApplicationCommandInteraction):
    pass

@poll.sub_command(
    description="Start a Waifu Poll"
)
async def start(
    inter:ApplicationCommandInteraction,
    autoClose:bool = commands.param(True,description="Whether to close this poll automatically based on Server options")
):
    
    await inter.response.defer()
    pollGuild = servers[inter.guild.id]
    if len(pollGuild.polls)!=0: #other polls have run
        if pollGuild.polls[-1].open: #another poll is running
            #TODO: include link to message
            await inter.send(responder.getResponse('WAIFU.POLL.EXISTS'),ephemeral=True)
            return
    message = await inter.original_message()
    newPoll=polls.Poll(message.id,pollGuild.options[guilds.Server.ServerOption.PollWaifuCount.value])
    pollGuild.addPoll(newPoll)
    # to run a poll:
    # 1 select options
    try:
        (names, sources) = newPoll.startPoll(pollGuild.waifus)
    except headpatExceptions.InsufficientOptionsError as err:
        await inter.send(responder.getResponse('WAIFU.POLL.INSUFFICIENT'),ephemeral=True)
        newPoll.endPoll(bot)
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
    # 5 accept input from buttons
    # handled in pollView
    # 6 poll end
    if (autoClose):
        delay = pollGuild.options[guilds.Server.ServerOption.PollParticipationCheckStartHours.value]
        delta=pollGuild.options[guilds.Server.ServerOption.PollParticipationCheckDeltaHours.value]
        end = pollGuild.options[guilds.Server.ServerOption.PollEndHours.value]
        threshold = pollGuild.options[guilds.Server.ServerOption.PollParticipationCheckCount.value]
        pollCog = PollCheckCog(delay,delta,end,newPoll,threshold)
        pollCog.checkPoll.start()
    # 7 update waifus

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
        await inter.send(responder.getResponse('WAIFU.POLL.NONE'))
        return
    if(poll.open):
        poll.endPoll(bot)
        await inter.send(responder.getResponse('WAIFU.POLL.CLOSE'))
    else:
        await inter.send(responder.getResponse('WAIFU.POLL.NONE'))

class PollCheckCog(commands.Cog):
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
        logger.info('Saving to database')
        for server in servers.values():
            database.storeGuildPickle(server)
        for waifuImage in glob.glob('*/*/*.qoi',root_dir=images.POLL_FOLDER):
            waifuData=waifuImage.split('/')
            imagePath=os.path.join(images.POLL_FOLDER,waifuImage)
            database.storeWaifuFile(waifuData[1],waifuData[0],imagePath)

    @storeDatabase.before_loop
    @storeFiles.before_loop
    async def waitForLoaded(self):
        await self.bot.wait_until_ready()

    async def loadFiles(self):
        allWaifus=database.getAllWaifus()
        for waifu in allWaifus:
            name=waifu[0]
            source=waifu[1]
            waifuImages = database.loadWaifu(name,source)
            for waifuImage in waifuImages:
                images.saveRawPollImage(waifuImage,hash(str(waifuImage)),images.sourceNameFolder(name,source))
        allGuilds=database.getAllGuilds()
        for guildId in allGuilds:
            database.getGuildPickle(guildId).save()

storageCog=StorageCog(bot)
bot.add_cog(storageCog)
asyncio.run(storageCog.loadFiles())
bot.run(TOKEN)