from asyncio import Lock, run
import logging, os
from statistics import stdev
from disnake import ApplicationCommandInteraction
from disnake.ext import commands, tasks
import database, images
import glob

class StorageCog(commands.Cog):
    def __init__(self,bot:commands.Bot):
        self.bot=bot
        self.logger=logging.getLogger(os.environ['LOGGER_NAME'])
        self.lock=Lock()
        self.loadFiles.start()
        self.storeFiles.start()
        self.storeDatabase.start()

    def cog_unload(self):
        self.logger.info('Storage Cog Unloading')
        self.loadFiles.cancel()
        self.storeFiles.cancel()
        self.storeDatabase.cancel()
        run(self.storeFiles())
        run(self.storeDatabase())

    @tasks.loop(hours=4)
    async def storeFiles(self):
        async with self.lock:
            self.logger.info('Saving Files')
            for server in self.bot.servers.values():
                server.save()

    @tasks.loop(hours=2)
    @storeFiles.after_loop
    async def storeDatabase(self):
        self.logger.info('Saving filesystem to database')
        async with self.lock:
            for server in self.bot.servers.values():
                database.storeGuildPickle(server)
            for waifuImage in glob.glob('*/*/*.qoi',root_dir=images.POLL_FOLDER):
                waifuData=waifuImage.split('/')
                imagePath=os.path.join(images.POLL_FOLDER,waifuImage)
                database.storeWaifuFile(waifuData[1],waifuData[0],imagePath,int(waifuData[2].replace('.qoi','')))

    @storeDatabase.before_loop
    @storeFiles.before_loop
    async def waitForLoaded(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=6)
    async def loadFiles(self):
        async with self.lock:
            self.logger.info('Fetching from Database to File System')
            allWaifus=database.getAllWaifus()
            for waifu in allWaifus:
                name=waifu[0]
                source=waifu[1]
                waifuHashes = database.getWaifuHashes(name,source)
                for waifuHash in waifuHashes:
                    waifuImage=database.loadWaifu(waifuHash)
                    images.saveRawPollImage(waifuImage,waifuHash,images.sourceNameFolder(name,source))
            allGuilds=database.getAllGuilds()
            for guildId in allGuilds:
                database.getGuildPickle(guildId).save()

class TestCog(commands.Cog):
    def __init__(self,bot:commands.Bot):
        self.bot=bot
    #put test commands here

    @commands.slash_command()
    async def cache(self, inter:ApplicationCommandInteraction):
        pass

    @commands.slash_command()
    async def ratings(self,inter):
        pass

    @ratings.sub_command()
    async def stdev(self,inter):
        await inter.send(f'stdev is {stdev([option.rating for option in self.bot.servers[inter.guild.id].waifus])}')
