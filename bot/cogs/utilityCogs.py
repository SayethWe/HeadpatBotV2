#python imports
from asyncio import Lock, run
import logging, os
from statistics import stdev
import glob
#local imports
import database, images
from headpatBot import HeadpatBot
from injections import folderWaifu
#library imports
from disnake import ApplicationCommandInteraction, File
from disnake.ext import commands, tasks
import yaml

class TimerCog(commands.Cog):
    def __init__(self,bot:HeadpatBot):
        self.bot=bot
        self.logger=logging.getLogger(os.environ['LOGGER_NAME'])
        self.dbLock=Lock()
        self.expiryLock=Lock()
        self.loadFiles.start()
        self.storeFiles.start()
        self.storeDatabase.start()
        self.expireWaifuClaims.start()

    def cog_unload(self):
        self.logger.info('Storage Cog Unloading')
        self.loadFiles.cancel()
        self.storeFiles.cancel()
        self.storeDatabase.cancel()
        run(self.storeFiles())
        run(self.storeDatabase())

    @tasks.loop(hours=4)
    async def storeFiles(self):
        async with self.dbLock:
            self.logger.info('Saving Files')
            for server in self.bot.servers.values():
                server.save()

    @tasks.loop(hours=2)
    @storeFiles.after_loop
    async def storeDatabase(self):
        self.logger.info('Saving filesystem to database')
        async with self.dbLock:
            for server in self.bot.servers.values():
                await database.storeGuildPickle(server)
            for waifuImage in glob.glob('*/*/*.qoi',root_dir=images.POLL_FOLDER):
                waifuTuple=waifuImage.split('/')
                imagePath=os.path.join(images.POLL_FOLDER,waifuImage)
                waifuData=await folderWaifu(waifuImage)
                await database.storeWaifuFile(waifuData,imagePath,int(waifuTuple[2].replace('.qoi','')))

    @storeDatabase.before_loop
    @storeFiles.before_loop
    async def waitForLoaded(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=6)
    async def loadFiles(self):
        async with self.dbLock:
            self.logger.info('Fetching from Database to File System')
            allWaifus=await database.getAllWaifus()
            for waifu in allWaifus:
                waifuHashes = await database.getWaifuHashes(waifu)
                for waifuHash in waifuHashes:
                    waifuImage=await database.loadWaifu(waifuHash)
                    images.saveRawPollImage(waifuImage,waifuHash,waifu)
            allGuilds=await database.getAllGuilds()
            for guildId in allGuilds:
                guild = await database.getGuildPickle(guildId)
                guild.save()

    @tasks.loop(hours=3)
    async def expireWaifuClaims(self):
        async with self.expiryLock:
            for serverId in self.bot.servers:
                self.bot.servers[serverId].releaseWaifus()

class HelpCog(commands.Cog):
    bufferLimit = 1750 #how many characters before we force dump
    with open(os.path.join("data","help.yaml"),"r") as file:
        try:
            helpOptions:dict[str,list[str]]=yaml.safe_load(file)
        except yaml.YAMLError as err:
            helpOptions = {'HelpFailure':['help failed to load']}
            logging.getLogger(os.environ['LOGGER_NAME']).error(err)

    def __init__(self,bot:HeadpatBot):
        self.bot=bot
        self.logger=logging.getLogger(os.environ['LOGGER_NAME'])

    @commands.slash_command()
    async def help(
        self,
        inter:ApplicationCommandInteraction,
        query:str = commands.Param(choices=[option for option in helpOptions])
    ):
        sendBuffer = ""
        for line in HelpCog.helpOptions[query]:
            bufferLen = len(sendBuffer)
            lineLen = len(line)
            if bufferLen + lineLen > HelpCog.bufferLimit:
                #send buffer, reset
                await inter.send(sendBuffer)
                sendBuffer = ""
            sendBuffer += line
            sendBuffer += '\n'
        #make sure we send everything
        if len(sendBuffer)>0:
            await inter.send(sendBuffer)

class TestCog(commands.Cog):
    def __init__(self,bot:HeadpatBot):
        self.bot=bot
    #put test commands here

    @commands.slash_command()
    async def cache(self, inter:ApplicationCommandInteraction):
        await inter.response.defer()
        server=self.bot.servers[inter.guild.id]
        with open('info.txt','w') as file:
            file.write(str(server))
        await database.storeGuildPickle(server)
        with open('info.txt','rb') as fileRaw:
            file=File(fileRaw,filename='info.txt')
            await inter.send(f'storing',file=file)

    @commands.slash_command()
    async def ratings(self,inter):
        pass

    @ratings.sub_command()
    async def stdev(self,inter):
        await inter.send(f'stdev is {stdev([option.rating for option in self.bot.servers[inter.guild.id].waifus])}')

    @commands.slash_command()
    async def add_tickets(self,inter,amt:int):
        self.bot.servers[inter.guild.id].modifyTickets(inter.author.id,amt)
        await inter.send('done',ephemeral=True)

    @commands.slash_command()
    async def error(self,inter):
        await inter.send('error raised')
        raise AttributeError