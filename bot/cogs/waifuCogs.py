#python imports
import os, logging
import glob, io
from aiohttp import ClientSession
#local imports
from headpatExceptions import *
from injections import WaifuData, folderWaifu, nameSourceWaifu, gachaWaifu
import images, database
from headpatBot import HeadpatBot
#library imports
from disnake import ApplicationCommandInteraction, Embed, File, Attachment, MessageInteraction, Webhook, ButtonStyle
from disnake.ui import Button
from disnake.ext import commands

class WaifuCog(commands.Cog):
    def __init__(self,bot:HeadpatBot):
        self.bot=bot
        self.logger=logging.getLogger(os.environ['LOGGER_NAME'])

    @commands.Cog.listener(name="on_button_click")
    async def waifuApprovalHandler(self,button_inter:MessageInteraction):
        data = button_inter.component.custom_id.split('|')
        if data[0] != 'approval':
            return
        await button_inter.response.defer()
        imageHash = int(data[1])
        if data[2] == 'accept':
            (imageArray,name,source) = await database.removeApproval(imageHash) #we've interacted. remove the approval, and get the data
            self.logger.debug(f'approving {name}|{source}')
            existingWaifu = images.saveRawPollImage(imageArray,imageHash,images.sourceNameFolder(name,source)) #throw into the filesystem
            await database.storeWaifu(name,source,imageArray,imageHash) #and into the database
            async with ClientSession() as session:
                announceHook = Webhook.from_url(os.environ['ANNOUNCE_HOOK'],session=session,bot_token=os.environ['DISCORD_TOKEN'])
                imageBytes = images.arrayToBytes(imageArray) #get image as bytes
                imageBytes.seek(0)
                attachment=File(imageBytes,filename=f'approved|{name}|{source}.png')
                if existingWaifu:
                    await self.bot.respond(announceHook,'WAIFU.ADD.ANNOUNCE.EXISTING',name,source,file = attachment)
                else:
                    await self.bot.respond(announceHook,'WAIFU.ADD.ANNOUNCE.NEW',name,source,file = attachment)
            await self.bot.respond(button_inter,'WAIFU.ADD.APPROVE',name)
            #set the buttons to allow removal
            removeButton=Button(label='remove',style=ButtonStyle.red,custom_id=f'approval|{imageHash}|remove')
            await button_inter.edit_original_message(components=removeButton)
        elif data[2] == 'reject':
            (*discard,name,source) = await database.removeApproval(imageHash) #we've interacted. remove the approval, and get the data
            self.logger.debug(f'rejecting {name}|{source}')
            await self.bot.respond(button_inter,'WAIFU.ADD.DENY',name)
            #remove the buttons
            await button_inter.edit_original_message(components=None)
        elif data[2] == 'remove':
            #remove waifu from:
            #database
            (name,source) = await database.removeWaifu(imageHash)
            self.logger.debug(f'removing {name}|{source}')
            # file system
            waifuGone = images.removePollImage(imageHash,images.sourceNameFolder(name,source))
            if waifuGone:
                # all servers
                for guildId in self.bot.servers:
                    try:
                        self.bot.servers[guildId].removeWaifu(name,source)
                    except WaifuDNEError:
                        pass
                await self.bot.respond(button_inter,'WAIFU.ADD.REMOVE.LAST',name)
                async with ClientSession() as session:
                    announceHook = Webhook.from_url(os.environ['ANNOUNCE_HOOK'],session=session,bot_token=os.environ['DISCORD_TOKEN'])
                    await self.bot.respond(announceHook,'WAIFU.ADD.ANNOUNCE.REMOVE',name,source)
            else:
                await self.bot.respond(button_inter,'WAIFU.ADD.REMOVE.ONE',name)
            #remove the buttons
            await button_inter.edit_original_message(components=None)

    # Headpat
    @commands.slash_command(
        description = "get headpats, up to four at a time."
    )
    async def headpat(
        self,
        inter:ApplicationCommandInteraction,
        qty:int=commands.Param(default=1,le=4,gt=0)
    ): #show 'randomly' selected headpat images
        for i in range(max(1,min(qty,4))):
            image=images.loadHeadpatImage()
            imageBytes=images.imageToBytes(image)
            attachment = File(imageBytes, filename = 'headpat.png')
            await self.bot.respond(inter,'HEADPAT.PASS',file=attachment)

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
        image:Attachment, 
        waifuData:WaifuData = commands.inject(nameSourceWaifu)
    ): #Sends a waifu to the approval channel
        if image.content_type.startswith('image'): #ensure it's actually an image
            name=waifuData.name
            source=waifuData.source
            await self.bot.respond(inter,'WAIFU.ADD.WAIT') #tell the user it's in consideration
            #send it off the the approval system
            imageHash=hash(image)
            imageBytes=io.BytesIO(await image.read())
            sendAttachment=await image.to_file()
            await database.addApproval(imageHash,images.bytesToArray(imageBytes),name,source)
            acceptButton=Button(label='accept',style=ButtonStyle.green,custom_id=f'approval|{imageHash}|accept')
            rejectButton=Button(label='reject',style=ButtonStyle.red,custom_id=f'approval|{imageHash}|reject')
            #get the channel to approve in (needs to be channel because buttons)
            announceChannel=self.bot.get_channel(os.environ['APPROVAL_CHANNEL'])
            if announceChannel is None:
                announceChannel = await self.bot.fetch_channel(os.environ['APPROVAL_CHANNEL'])
            await self.bot.respond(announceChannel,'WAIFU.ADD.ASK',name,source,
                components=[acceptButton,rejectButton],
                file=sendAttachment)
        else:
            await self.bot.respond(inter,'WAIFU.ADD.NOT_IMAGE')

    @waifu.sub_command(
        description="Show an image of a waifu from the global database"
    )
    async def show(
        self,
        inter:ApplicationCommandInteraction,
        waifuData:WaifuData = commands.inject(folderWaifu)
    ):
        await inter.response.defer()
        name=waifuData.name
        source=waifuData.source
        try:
            image = images.loadPollImage(images.sourceNameFolder(name,source))
        except WaifuDNEError:
            await self.bot.respond(inter,'WAIFU.ERROR.DNE',name,source)
            return
        imageBytes = images.imageToBytes(image)
        attachment = File(imageBytes, filename = f'{name}.png')
        embed=Embed(title=waifuData)
        embed.set_image(file=attachment)
        #check the server to see if we can add extra information
        try:
            serverSide=self.bot.servers[inter.guild.id].getWaifuByNameSource(name,source)
            #waifu exists in server
            #add rating and claim info
            if serverSide.claimer == 0:
                #unclaimed
                footer_text=self.bot.getResponse('WAIFU.SHOW.FOOTER.UNCLAIMED',serverSide.rating)
            else:
                claimer = await inter.guild.getch_member(serverSide.claimer)
                footer_text=self.bot.getResponse('WAIFU.SHOW.FOOTER.CLAIMED',serverSide.rating,claimer.display_name,serverSide.claimedAt.strftime("%Y/%m/%d %H:%M %Z"))
            embed.set_footer(text=footer_text)
        except WaifuDNEError:
            pass #waifu did not exist serverside
        await self.bot.respond(inter,'WAIFU.SHOW.PASS',embed=embed)

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
                reply = self.bot.getResponse('WAIFU.LIST.GLOBAL',count)
            elif scope == 'Local':
                waifus=self.bot.servers[inter.guild.id].waifus
                reply = self.bot.getResponse('WAIFU.LIST.LOCAL',len(waifus))
                for waifu in waifus:
                    waifuList.write(f"{waifu}\n")
            else:
                count=0
                for waifuStr in glob.glob('*/*/',root_dir=images.POLL_FOLDER):
                    (source,name,*discard) = waifuStr.split('/')
                    if not self.bot.servers[inter.guild.id].getWaifuByNameSource(name,source):
                        waifuList.write(f'{name} from {source}\n')
                        count+=1
                reply = self.bot.getResponse('WAIFU.LIST.DIFFERENCE',count)
        with open('Waifus.txt','rb') as waifuList:
            file = File(waifuList, filename='Waifus.txt')
            await self.bot.send(inter,reply,file=file,ephemeral=True)

class GachaCog(commands.Cog):
    def __init__(self,bot:HeadpatBot):
        self.bot=bot
        self.logger=logging.getLogger(os.environ['LOGGER_NAME'])

    @commands.slash_command()
    async def tickets(self,inter:ApplicationCommandInteraction):
        pass

    @tickets.sub_command()
    async def get(self,inter:ApplicationCommandInteraction):
        await self.bot.respond(inter,'TICKETS.GET',self.bot.servers[inter.guild.id].getTickets(inter.author.id),ephemeral=True)

    @commands.slash_command(    )
    async def gacha(
        self,
        inter:ApplicationCommandInteraction
    ):
        pass

    @gacha.sub_command(
        description="Roll and claim a server waifu"
    )
    async def roll(
        self,
        inter:ApplicationCommandInteraction,
        spend:int=commands.Param(ge=1)
    ):
        await inter.response.defer()
        userId=inter.author.id
        server=self.bot.servers[inter.guild.id]
        try:
            #remove tickets
            server.modifyTickets(userId,-spend)
            #roll a waifu
            selected=server.waifuRoll(userId,spend)
            #do the alert
            await self.bot.respond(inter,'GACHA.ROLL.SUCCESS',selected.name,selected.source)
        except InsufficientTicketsError:
            await self.bot.respond(inter,'GACHA.ROLL.INSUFFICIENT',ephemeral=True)
        except InsufficientOptionsError:
            await self.bot.respond(inter,'GACHA.ROLL.NONE',ephemeral=True)
            server.modifyTickets(userId,spend)
        except UnreachableOptionsError:
            await self.bot.respond(inter,'GACHA.ROLL.OUT_OF_RANGE',ephemeral=True)
        except CollectionFullError:
            await self.bot.respond(inter,'GACHA.ROLL.FULL',ephemeral=True)

    @gacha.sub_command(
        description="see your claimed waifus"
    )   
    async def collection(
        self,
        inter:ApplicationCommandInteraction
    ):
        server=self.bot.servers[inter.guild.id]
        claimed=server.claimedWaifus(inter.author.id)
        await inter.send(claimed)
