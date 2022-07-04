#python imports
import logging, os
#local imports
from headpatExceptions import WaifuConflictError, WaifuDNEError
from guilds import Server
from headpatBot import HeadpatBot
from injections import WaifuData, serverWaifu, missingWaifu
#library imports
from disnake import ApplicationCommandInteraction, Permissions, Attachment, File
from disnake.ext import commands

class ManageWaifusCog(commands.Cog):
    def __init__(self, bot:HeadpatBot):
        self.bot=bot
        self.logger=logging.getLogger(os.environ['LOGGER_NAME'])

    @commands.slash_command(
        default_member_permission=Permissions(manage_messages=True),
        dm_permission=False
    )
    async def manage_waifus(
        self,
        inter:ApplicationCommandInteraction
    ):
        pass

    @manage_waifus.sub_command(
        description = "add a waifu to future polls on this server"
    )
    async def pull(
        self,
        inter:ApplicationCommandInteraction,
        waifuData:WaifuData = commands.inject(missingWaifu)
    ):
        name=waifuData.name
        source=waifuData.source
        try:
            self.bot.servers[inter.guild.id].addWaifu(name,source)
            await self.bot.respond(inter,'WAIFU.PULL.PASS',name,source)
        except WaifuConflictError:
            await self.bot.respond(inter,'WAIFU.ERROR.CONFLICT',name,source)
        except WaifuDNEError:
            await self.bot.respond(inter,'WAIFU.ERROR.DNE',name,source)

    @manage_waifus.sub_command(
        description="remove a waifu from further polls on this server"
    )
    async def remove(
        self,
        inter:ApplicationCommandInteraction,
        waifuData:WaifuData = commands.inject(serverWaifu)
    ):
        name=waifuData.name
        source=waifuData.source
        try:
            self.bot.servers[inter.guild.id].removeWaifu(name,source)
            await self.bot.respond(inter,'WAIFU.REMOVE.PASS',name,source)
        except WaifuDNEError:
            await self.bot.respond(inter,'WAIFU.ERROR.DNE',name,source)

    @manage_waifus.sub_command(
        description="add a whole list of waifus defined in a CSV to your server"
    )
    async def pull_csv(
        self,
        inter:ApplicationCommandInteraction,
        csv:Attachment, 
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
                    self.logger.debug(waifu)
                    waifu=waifu.replace('\r','').replace('\n','').strip()
                    info=waifu.split(',')
                    try:
                        self.bot.servers[inter.guild.id].addWaifu(info[0],info[1])
                    except WaifuDNEError:
                        numFailed+=1
                        failedList.write(f'unable to find in database: {waifu}\n')
                    except WaifuConflictError:
                        numFailed+=1
                        failedList.write(f'already present in server:  {waifu}\n')
                    except IndexError:
                        #must have reached a dead line
                        pass

            if(numFailed>0):
                with open(f"failedList{inter.guild.id}.txt",'rb') as failedList:
                    file = File(failedList,filename="Failed Waifus.txt")
                    await self.bot.respond(inter,'WAIFU.PULL.CSV.PASS', len(waifus)-numFailed,file=file,ephemeral=True)
            else:
                await self.bot.respond(inter,'WAIFU.PULL.CSV.PASS', len(waifus))
        else:
            await self.bot.respond(inter,'WAIFU.PULL.CSV.NOT_CSV',ephemeral=True)

class ServerOptionsCog(commands.Cog):
    def __init__(self,bot:HeadpatBot):
        self.bot=bot
        self.logger=logging.getLogger(os.environ['LOGGER_NAME'])

    @commands.slash_command(
        description="set server options"
    )
    async def options(
        self,
        inter:ApplicationCommandInteraction,
        setting:Server.ServerOption=commands.Param(description="option to set"),
        set_value:int= commands.Param(default=-1,ge=0,description="value to set option to")
    ):
        guild=self.bot.servers[inter.guild.id]
        if set_value == -1:
            #show value
            await self.bot.respond(inter,'OPTION.GET',setting,guild.options[setting])
        else:
            #set value
            guild.options[setting]=set_value
            await self.bot.respond(inter,'OPTION.SET',setting,set_value)