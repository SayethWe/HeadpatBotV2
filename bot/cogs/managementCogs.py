import logging, os
from disnake.ext import commands
from injections import WaifuData
import disnake
from disnake import ApplicationCommandInteraction
import responder
from headpatExceptions import WaifuConflictError, WaifuDNEError
from guilds import Server

class ManageWaifusCog(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot=bot
        self.logger=logging.getLogger(os.environ['LOGGER_NAME'])

    @commands.slash_command(
        default_permission=disnake.Permissions(manage_messages=True),
        dm_permission=False
    )
    async def manageWaifus(
        self,
        inter:ApplicationCommandInteraction
    ):
        pass

    @manageWaifus.sub_command(
        description = "add a waifu to future polls on this server"
    )
    async def pull(
        self,
        inter:ApplicationCommandInteraction,
        waifuData:WaifuData
    ):
        name=waifuData.name
        source=waifuData.source
        try:
            self.bot.servers[inter.guild.id].addWaifu(name,source)
            reply=responder.getResponse('WAIFU.PULL.PASS',name,source)
        except WaifuConflictError:
            reply=responder.getResponse('WAIFU.ERROR.CONFLICT',name,source)
        except WaifuDNEError:
            reply=responder.getResponse('WAIFU.ERROR.DNE',name,source)
        await inter.send(reply)

    @manageWaifus.sub_command(
        description="remove a waifu from further polls on this server"
    )
    async def remove(
        self,
        inter:ApplicationCommandInteraction,
        waifuData:WaifuData
    ):
        name=waifuData.name
        source=waifuData.source
        try:
            self.bot.servers[inter.guild.id].removeWaifu(name,source)
            reply=responder.getResponse('WAIFU.REMOVE.PASS',name,source)
        except WaifuDNEError:
            reply=responder.getResponse('WAIFU.ERROR.DNE',name,source)
        await inter.send(reply)

    @manageWaifus.sub_command(
        description="add a whole list of waifus defined in a CSV to your server"
    )
    async def pullCSV(
        self,
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
                    self.logger.debug(waifu)
                    waifu=waifu.replace('\r','').replace('\n','')
                    info=waifu.split(',')
                    try:
                        self.bot.servers[inter.guild.id].addWaifu(info[0],info[1])
                    except WaifuDNEError:
                        numFailed+=1
                        failedList.write(f'unable to find in database: {waifu}\n')
                    except WaifuConflictError:
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

class ServerOptionsCog(commands.Cog):
    def __init__(self,bot:commands.Bot):
        self.bot=bot
        self.logger=logging.getLogger(os.environ['LOGGER_NAME'])

    @commands.slash_command(
        description="set server options"
    )
    async def options(
        self,
        inter:ApplicationCommandInteraction,
        setting:Server.ServerOption=commands.Param(description="option to set"),
        setValue:int= commands.Param(default=-1,ge=0,description="value to set option to")
    ):
        guild=self.bot.servers[inter.guild.id]
        if setValue == -1:
            #show value
            await inter.send(responder.getResponse('OPTION.GET',setting,guild.options[setting]))
        else:
            #set value
            guild.options[setting]=setValue
            await inter.send(responder.getResponse('OPTION.SET',setting,setValue))