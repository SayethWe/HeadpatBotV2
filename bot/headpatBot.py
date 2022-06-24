import os, logging
from pickle import UnpicklingError
import disnake
from disnake import Interaction, ApplicationCommandInteraction, File, Webhook
from disnake.abc import GuildChannel
from disnake.ext import commands
import yaml
from numpy.random import default_rng
from glom import glom
import database
from guilds import Server

class HeadpatBot(commands.InteractionBot):
    def __init__(self,*args,**kwargs):
        self.logger=logging.getLogger(os.environ['LOGGER_NAME'])
        with open(os.path.join("bot","responses.yaml"),"r") as file:
            try:
                self.responses = yaml.safe_load(file)
            except yaml.YAMLError as err:
                self.logger.error(err)
        self.rng=default_rng()
        self.servers=dict[int,Server]()
        #enumerate our intents
        intents = disnake.Intents(
            guilds=True #in order to access the announcement channel, and load servers
        )
        help_command=commands.DefaultHelpCommand()
        super().__init__(intents=intents,help_command=help_command,*args,**kwargs)
        
    #Events
    async def on_ready(self): #events to fire on a sucessful reconnection
        self.logger.info(f"Logging in as {self.user}")
        for guild in self.guilds:
            try:
                self.servers[guild.id] = await database.getGuildPickle(guild.id)  # only place database is used
            except (UnpicklingError, TypeError):
                self.servers[guild.id]=Server.load(guild.id)
            self.logger.info(f"loading server {guild.name} with id {guild.id}")
        self.logger.info('bot is ready')

    async def on_disconnect(self): #events to fire when closing
        self.logger.flush()
        storageCog = self.get_cog('StorageCog')
        await storageCog.storeFiles()
        await storageCog.storeDatabase()

    async def on_slash_command_error(
        self,
        inter:ApplicationCommandInteraction,
        err:commands.CommandError
    ): #events to fire when something goes wrong
        try:
            self.logger.exception(f'Slash Command Error from {inter.guild.name}|{inter.channel.name}',stack_info=True,exc_info=err)
            if isinstance(err,commands.CheckFailure): #should never run now, but keep in just in case.
                await self.respond(inter,'ERROR.NOT_PERMITTED',ephemeral=True)
            elif isinstance(err,commands.MissingRequiredArgument):
                await self.respond(inter,'ERROR.ARGUMENT',ephemeral=True)
            else:
                await self.respond(inter,'ERROR.GENERIC',ephemeral=True)
        except Exception as err2:
            #last ditch effort to get some info to the log and user
            self.logger.critical(err)
            self.logger.critical(f'an error occured while handling previous error: {err2}')

    ### help command TODO
    @commands.slash_command(
        description="Get command and bot documentation"
    )
    async def help(
        self,
        inter: ApplicationCommandInteraction
    ): #dump the README to the user
        await self.respond(inter,'HELP',file=File("README.md"),ephemeral=True)

    async def respond(self,sendable:Interaction|Webhook|GuildChannel,request:str,*args:str,**kwargs):
        reply=self.getResponse(request,*args)
        await self.send(sendable,reply,**kwargs)

    async def send(self,sendable:Interaction|Webhook|GuildChannel,reply:str,**kwargs):
        await sendable.send(content=reply,**kwargs)

    def getResponse(self,request:str,*args:str):
        request=request.upper()
        replies:list[str] = glom(self.responses,request)
        reply:str = self.rng.choice(replies)
        reply=reply.replace('[NEWLINE]','\n')
        reply=reply.format(*args)
        return reply
