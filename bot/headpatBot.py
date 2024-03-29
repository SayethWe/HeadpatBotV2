import os, logging
from aiohttp import ClientSession
import disnake
from disnake import Interaction, ApplicationCommandInteraction, File, Webhook, Guild
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
        with open(os.path.join("data","responses.yaml"),"r") as file:
            try:
                self.responses = yaml.safe_load(file)
            except yaml.YAMLError as err:
                self.logger.error(err)
        self.rng=default_rng()
        self.servers=dict[int,Server]()
        #enumerate our intents
        intents = disnake.Intents(
            guilds=True, #in order to access the announcement channel, and load servers
            members=True, #to display usernames and nicknames, esp. in waifu show               Priveleged Intent
        )
        help_command=commands.DefaultHelpCommand()
        super().__init__(intents=intents,help_command=help_command,*args,**kwargs)
        
    #Events
    async def on_ready(self): #events to fire on a sucessful reconnection
        self.logger.info(f"Logging in as {self.user}")
        for guild in self.guilds:
            try:
                server = await database.getGuild(guild.id)  # place 1 database is used
                server.save()
            except Exception:
                pass
            self.servers[guild.id]=Server.load(guild.id)
            self.logger.info(f"loading server {guild.name} with id {guild.id}")
            await database.storeGuild(self.servers[guild.id])
        self.logger.info('bot is ready')

    async def on_disconnect(self): #events to fire when closing
        self.logger.flush()
        #storageCog = self.get_cog('StorageCog')
        #await storageCog.storeFiles()
        #await storageCog.storeDatabase()

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
                if 'LOGS_HOOK' in os.environ:
                    self.logger.warning('Error unhandled, dumping log to webhook')
                    async with ClientSession() as session:
                        with open('discord.log','rb') as file:
                            logHook = Webhook.from_url(os.environ['LOGS_HOOK'],session=session,bot_token=os.environ['DISCORD_TOKEN'])
                            file.seek(0,os.SEEK_END) #go to the end so we can get file size
                            file.seek(max(-4*2**20,-file.tell()),os.SEEK_END) #get the last bit (4MiB) of the file, or if it's smaller, all of it.
                            attachment = File(file)
                            await self.send(logHook,'log dump',file=attachment)
        except Exception as err2:
            #last ditch effort to get some info to the log and user
            self.logger.critical(err)
            self.logger.critical(f'an error occured while handling previous error: {err2}')

    async def on_guild_join(
        self,
        guild:Guild
    ):
        #add to list
        s = Server(guild.id)
        self.logger.info(f'new guild {guild.name}\n {str(s)}')
        self.servers[guild.id]=s
        #save pickle
        s.save()
        #add to database
        await database.storeGuild(s)                # place 2 database is used

    async def on_guild_remove(
        self,
        guild:Guild
    ):
        #remove from list
        s=self.servers.pop(guild.id)
        self.logger.info(f'leaving guild {guild.id}|{guild.name}')
        #delete file
        s.delete()
        #remove from database
        await database.removeGuild(guild.id)              # place 3 database is used

    ### help command TODO
    #@commands.slash_command(
    #    description="Get command and bot documentation"
    #)
    #async def help(
    #    self,
    #    inter: ApplicationCommandInteraction
    #): #dump the README to the user
    #    await self.respond(inter,'HELP',file=File("README.md"),ephemeral=True)

    async def respond(self,sendable:Interaction|Webhook|GuildChannel,request:str,*args:str,**kwargs):
        reply=self.getResponse(request,*args)
        await self.send(sendable,reply,**kwargs)

    async def send(self,sendable:Interaction|Webhook|GuildChannel,reply:str,**kwargs):
        await sendable.send(content=reply,**kwargs)

    def getResponse(self,request:str,*args:str):
        request=request.upper()
        replies:list[str] = glom(self.responses,request)
        reply:str = self.rng.choice(replies)
        reply=reply.format(*args)
        return reply
