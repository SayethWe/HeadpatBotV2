import os, logging
from disnake.ext import commands
from injections import WaifuData
from disnake import ApplicationCommandInteraction, File
import disnake
import glob
import responder, approval, images

class WaifuCog(commands.Cog):
    def __init__(self,bot:commands.Bot):
        self.bot=bot
        self.logger=logging.getLogger(os.environ['LOGGER_NAME'])

    @commands.slash_command()
    async def waifu(
        self,
        inter:ApplicationCommandInteraction
    ): #Parent command. Code here is run for all subcommands
        pass

    @waifu.sub_command(
        description="Suggest a waifu and/or image for inclusion in the bot"
    )
    async def suggest(
        self,
        inter:ApplicationCommandInteraction,
        image:disnake.Attachment, 
        waifuData:WaifuData
    ): #Sends a waifu to the approval channel
        if image.content_type.startswith('image'): #ensure it's actually an image
            name=waifuData.name
            source=waifuData.source
            await inter.send(responder.getResponse('WAIFU.ADD.WAIT')) #tell the user it's in consideration
            await approval.getWaifuApproval(self.bot,image,name,source) #send it off the the approval system
        else:
            await inter.send(responder.getResponse('WAIFU.ADD.NOT_IMAGE'))

    @waifu.sub_command(
        description="Show an image of a waifu from the global database"
    )
    async def show(
        self,
        inter:ApplicationCommandInteraction,
        waifuData:WaifuData
    ):
        name=waifuData.name
        source=waifuData.source
        image = images.loadPollImage(images.sourceNameFolder(source,name))
        imageBytes = images.imageToBytes(image)
        attachment = File(imageBytes, filename = f'{name}.png')
        reply = responder.getResponse('WAIFU.SHOW.PASS')
        await inter.send(reply,file=attachment)

    @waifu.sub_command(
        description="get a list of waifus, either in this server, or available for pulls"
    )
    async def getList(
        self,
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
                waifus=self.bot.servers[inter.guild.id].waifus
                reply = responder.getResponse('WAIFU.LIST.LOCAL',len(waifus))
                for waifu in waifus:
                    waifuList.write(f"{waifu}\n")
            else:
                count=0
                for waifuStr in glob.glob('*/*/',root_dir=images.POLL_FOLDER):
                    (source,name,*discard) = waifuStr.split('/')
                    if not self.bot.servers[inter.guild.id].getWaifuByNameSource(name,source):
                        waifuList.write(f'{name} from {source}\n')
                        count+=1
                reply = responder.getResponse('WAIFU.LIST.DIFFERENCE',count)
        with open('Waifus.txt','rb') as waifuList:
            file = disnake.File(waifuList, filename='Waifus.txt')
            await inter.send(reply,file=file,ephemeral=True)

    