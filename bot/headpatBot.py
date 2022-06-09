import os, sys, logging
from discord_webhook_logging import DiscordWebhookHandler
os.environ['LOGGER_NAME']='disnake'

#get the logger
logger = logging.getLogger(os.environ['LOGGER_NAME'])
logger.setLevel(logging.DEBUG)
format=logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

#debug file handler
fhandler = logging.FileHandler(filename='discord.log', encoding = 'utf-8', mode = 'w')
fhandler.setLevel('DEBUG')
fhandler.setFormatter(format)
logger.addHandler(fhandler)

#info console handler
chandler = logging.StreamHandler(stream = sys.stdout)
chandler.setFormatter(format)
chandler.setLevel('INFO')
logger.addHandler(chandler)

#warning webhook handler, if a link exists
if 'LOGS_HOOK' in os.environ:
    whandler = DiscordWebhookHandler(webhook_url=os.environ['LOGS_HOOK'])
    whandler.setLevel('WARNING')
    logger.addHandler(whandler)

import asyncio
from pickle import UnpicklingError
import disnake
from disnake import ApplicationCommandInteraction, File
from disnake.ext import tasks, commands
import images, responder, guilds, polls, database
from cogs.pollCog import PollCog
from cogs.utilityCogs import StorageCog, TestCog
from cogs.managementCogs import ManageWaifusCog
from cogs.waifuCogs import WaifuCog, GachaCog

TOKEN=os.environ['DISCORD_TOKEN']
#set up our intents
#guilds: I forget why, actually.
intents = disnake.Intents(guilds=True)

#set up the bot
if 'TEST_ENV' in os.environ:
    #development version
    bot=commands.Bot(
        intents=intents,
        test_guilds=[int(g) for g in os.environ['TEST_ENV'].split(",")],
        help_command=commands.DefaultHelpCommand()
    )
else:
     bot=commands.Bot(
        intents=intents,
        help_command=commands.DefaultHelpCommand()
    )

bot.servers=dict[int,guilds.Server]()

# Events
@bot.event
async def on_ready(): #events to fire on a sucessful reconnection
    logger.info(f"Logging in as {bot.user}")
    for guild in bot.guilds:
        try:
            bot.servers[guild.id] = database.getGuildPickle(guild.id)
        except (UnpicklingError, TypeError):
            bot.servers[guild.id]=guilds.Server.load(guild.id)
        logger.info(f"loading server {guild.name} with id {guild.id}")
    logger.info('bot is ready')

@bot.event
async def on_disconnect(): #events to fire when closing
    logger.flush()
    storageCog = bot.get_cog('StorageCog')
    await storageCog.storeFiles()
    await storageCog.storeDatabase()

@bot.event
async def on_slash_command_error(
    inter:ApplicationCommandInteraction,
    err:commands.CommandError
): #events to fire when something goes wrong
    try:
        logger.exception(f'Slash Command Error from {inter.guild.name}|{inter.channel.name}',stack_info=True,exc_info=err)
        if isinstance(err,commands.CheckFailure): #should never run now, but keep in just in case.
            await inter.send(responder.getResponse('ERROR.NOT_PERMITTED'),ephemeral=True)
        elif isinstance(err,commands.MissingRequiredArgument):
            await inter.send(responder.getResponse('ERROR.ARGUMENT'),ephemeral=True)
        else:
            await inter.send(responder.getResponse('ERROR.GENERIC'),ephemeral=True)
    except Exception as err2:
        #last ditch effort to get some info to the log and user
        logger.critical(err)
        logger.critical(f'an error occured while handling previous error: {err2}')

### help command TODO
@bot.slash_command(
    description="Get command and bot documentation"
)
async def help(
    inter: ApplicationCommandInteraction
): #dump the README to the user
    await inter.send(responder.getResponse('HELP'),file=File("README.md"),ephemeral=True)

# Headpat
@bot.slash_command(
    description = "get headpats, up to four at a time."
)
async def headpat(
    inter:ApplicationCommandInteraction,
    qty:int=commands.Param(default=1,le=4,gt=0)
): #show 'randomly' selected headpat images
    for i in range(max(1,min(qty,4))):
        image=images.loadHeadpatImage()
        imageBytes=images.imageToBytes(image)
        attachment = File(imageBytes, filename = 'headpat.png')
        await inter.send(responder.getResponse('HEADPAT.PASS'),file=attachment)


class PollCheck: #Unused class for automaticall closing polls
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

#register the cogs
bot.add_cog(StorageCog(bot))
bot.add_cog(PollCog(bot))
bot.add_cog(ManageWaifusCog(bot))
bot.add_cog(WaifuCog(bot))
bot.add_cog(GachaCog(bot))
if 'TEST_ENV' in os.environ:
    #devopment commands
    bot.add_cog(TestCog(bot))
bot.run(TOKEN)