#python imports
import os, logging
import glob, io
from aiohttp import ClientSession
#local imports
from headpatExceptions import *
from injections import WaifuData, folderWaifu, nameSourceWaifu, gachaWaifu
import images, database
from headpatBot import HeadpatBot
from guilds import ServerOption
#library imports
from disnake import ApplicationCommandInteraction, Embed, File, Attachment, MessageInteraction, ModalInteraction, Webhook, ButtonStyle
from disnake.ui import Button, Modal, TextInput
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
        imageHash = int(data[1])
        if data[2] == 'accept':
            await button_inter.response.defer() #inside if statement because modals have issues with defered responses
            (imageArray,waifuData) = await database.removeApproval(imageHash) #we've interacted. remove the approval, and get the data
            self.logger.debug(f'approving {waifuData}')
            existingWaifu = images.saveRawPollImage(imageArray,imageHash,waifuData) #throw into the filesystem
            await database.storeWaifu(waifuData,imageArray,imageHash) #and into the database
            async with ClientSession() as session:
                announceHook = Webhook.from_url(os.environ['ANNOUNCE_HOOK'],session=session,bot_token=os.environ['DISCORD_TOKEN'])
                imageBytes = images.arrayToBytes(imageArray) #get image as bytes
                imageBytes.seek(0)
                attachment=File(imageBytes,filename=f'approved|{waifuData}.png')
                if existingWaifu:
                    await self.bot.respond(announceHook,'WAIFU.ADD.ANNOUNCE.EXISTING',waifuData.name,waifuData.source,file = attachment)
                else:
                    await self.bot.respond(announceHook,'WAIFU.ADD.ANNOUNCE.NEW',waifuData.name,waifuData.source,file = attachment)
            await self.bot.respond(button_inter,'WAIFU.ADD.APPROVE',waifuData.name)
            #set the buttons to allow removal
            removeButton=Button(label='remove',style=ButtonStyle.red,custom_id=f'approval|{imageHash}|remove')
            await button_inter.message.edit(components=removeButton)
        elif data[2] == 'reject':
            (*discard,waifuData) = await database.removeApproval(imageHash) #we've interacted. remove the approval, and ignore the data
            self.logger.debug(f'rejecting {waifuData}')
            await self.bot.respond(button_inter,'WAIFU.ADD.DENY',waifuData.name)
            #remove the buttons
            await button_inter.message.edit(components=None)
        elif data[2] == 'modify':
            oldWaifu = await database.getApproval(imageHash)
            #create and send an edit modal
            editName = TextInput(label = "edit waifu name",custom_id=f"editName",value=oldWaifu.name)
            editSource = TextInput(label = "edit waifu name",custom_id=f"editSource",value=oldWaifu.source)
            await button_inter.response.send_modal(
                title='edit waifu approval',
                components=[editName,editSource],
                custom_id=f'approval|{imageHash}|editModal|{button_inter.id}')
        elif data[2] == 'remove':
            #remove waifu from:
            #database
            waifuData = await database.removeWaifu(imageHash)
            self.logger.debug(f'removing {waifuData}')
            # file system
            waifuGone = images.removePollImage(imageHash,waifuData)
            if waifuGone:
                # all servers
                for guildId in self.bot.servers:
                    try:
                        self.bot.servers[guildId].removeWaifu(waifuData)
                    except WaifuDNEError:
                        pass
                await self.bot.respond(button_inter,'WAIFU.ADD.REMOVE.LAST',waifuData.name)
                async with ClientSession() as session:
                    announceHook = Webhook.from_url(os.environ['ANNOUNCE_HOOK'],session=session,bot_token=os.environ['DISCORD_TOKEN'])
                    await self.bot.respond(announceHook,'WAIFU.ADD.ANNOUNCE.REMOVE',waifuData.name,waifuData.source)
            else:
                await self.bot.respond(button_inter,'WAIFU.ADD.REMOVE.ONE',waifuData.name)
            #remove the buttons
            await button_inter.message.edit(components=None)

    @commands.Cog.listener(name="on_modal_submit")
    async def approvalEditHandler(self,modal_inter:ModalInteraction):
        data = modal_inter.custom_id.split('|')
        if data[0] != 'approval':
            return
        imageHash = int(data[1])
        newName = modal_inter.text_values['editName']
        newSource = modal_inter.text_values['editSource']
        await modal_inter.message.edit(content=self.bot.getResponse('WAIFU.ADD.ASK',newName,newSource))
        await database.modifyApproval(imageHash,WaifuData(newName,newSource))
        await self.bot.respond(modal_inter,'WAIFU.ADD.EDIT',newName,ephemeral=True)

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
            imageHash=hash(image)
            #check to be sure image does not exist
            try:
                existingData=await database.loadWaifu(imageHash)
            except AttributeError:
                existingData = None
            if existingData is not None:
                await self.bot.respond(inter,'WAIFU.ADD.EXISTS')
                return
            #or that it's not waiting for approval
            try:
                existingData=await database.getApproval(imageHash)
            except AttributeError:
                existingData=None
            if existingData is not None:
                await self.bot.respond(inter,'WAIFU.ADD.APPROVING')
                return
            await self.bot.respond(inter,'WAIFU.ADD.WAIT') #tell the user it's in consideration
            #send it off the the approval system
            imageBytes=io.BytesIO(await image.read())
            sendAttachment=await image.to_file()
            await database.addApproval(imageHash,images.bytesToArray(imageBytes),waifuData)
            acceptButton=Button(label='accept',style=ButtonStyle.green,custom_id=f'approval|{imageHash}|accept')
            editButton=Button(label='edit',style=ButtonStyle.blurple,custom_id=f'approval|{imageHash}|modify')
            rejectButton=Button(label='reject',style=ButtonStyle.red,custom_id=f'approval|{imageHash}|reject')
            #get the channel to approve in (needs to be channel because buttons)
            announceChannel=self.bot.get_channel(os.environ['APPROVAL_CHANNEL'])
            if announceChannel is None:
                announceChannel = await self.bot.fetch_channel(os.environ['APPROVAL_CHANNEL'])
            await self.bot.respond(announceChannel,'WAIFU.ADD.ASK',waifuData.name,waifuData.source,
                components=[acceptButton,editButton,rejectButton],
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
        try:
            image = images.loadPollImage(waifuData)
        except WaifuDNEError:
            await self.bot.respond(inter,'WAIFU.ERROR.DNE',waifuData.name,waifuData.source)
            return
        imageBytes = images.imageToBytes(image)
        attachment = File(imageBytes, filename = f'{waifuData}.png')
        #check the server to see if we can add extra information
        try:
            serverSide=self.bot.servers[inter.guild.id].getWaifu(waifuData)
            #waifu exists in server
            #add rating and claim info
            if serverSide.claimer == 0:
                #unclaimed
                await self.bot.respond(inter,'WAIFU.SHOW.UNCLAIMED',waifuData, serverSide.rating,file=attachment)
            else:
                claimer = await inter.guild.getch_member(serverSide.claimer)
                await self.bot.respond(inter,'WAIFU.SHOW.CLAIMED', waifuData,
                    serverSide.rating, claimer.display_name,
                    int(serverSide.claimedAt.timestamp()),serverSide.level,
                    file=attachment)
        except WaifuDNEError:
            await self.bot.respond(inter,'WAIFU.SHOW.GLOBAL',waifuData,file=attachment)

    @waifu.sub_command(
        description="get a list of waifus, either in this server, or available for pulls"
    )
    async def get_list(
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
                    waifuData = await folderWaifu(waifuStr)
                    waifuList.write(f'{waifuData}\n')
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
                    waifuData = await folderWaifu(waifuStr)
                    try:
                        self.bot.servers[inter.guild.id].getWaifu(waifuData)
                    except WaifuDNEError:
                        waifuList.write(f'{waifuData}\n')
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
        await self.bot.respond(inter,'GACHA.LIST',len(claimed),'\n'.join([f'__{claim.name}__ of __{claim.source}__' for claim in claimed]))

    @gacha.sub_command(
        description="unclaim a waifu and get some tickets back"
    )
    async def remove(
        self,
        inter:ApplicationCommandInteraction,
        waifuData:WaifuData = commands.inject(gachaWaifu)
    ):
        server=self.bot.servers[inter.guild.id]
        try:
            waifu=server.getWaifu(waifuData)
            if waifu.claimer != inter.author.id:
                await self.bot.respond(inter,'GACHA.RELEASE.NOT_OWNER')
                return
            refund = int(0.75*server.timeLeft(waifu)/server.getOption(ServerOption.GachaExpiryHours)*waifu.rating)
            server.modifyTickets(inter.author.id,refund)
            waifu.release()
            await self.bot.respond(inter,'GACHA.RELEASE.SUCCESS',refund)
        except WaifuDNEError:
            await self.bot.respond(inter,'WAIFU.ERROR.NOT_IN_SERVER')

    @gacha.sub_command(
        description="spend some tickets to improve a waifu"
    )
    async def improve(
        self,
        inter:ApplicationCommandInteraction,
        waifuData:WaifuData = commands.inject(gachaWaifu)
    ):
        server=self.bot.servers[inter.guild.id]
        try:
            waifu=server.getWaifu(waifuData)
            if waifu.claimer != inter.author.id:
                await self.bot.respond(inter,'GACHA.IMPROVE.NOT_OWNER')
                return
            cost = waifu.level*waifu.rating
            try:
                server.modifyTickets(inter.author.id,-cost)
                waifu.improve()
                await self.bot.respond(inter,'GACHA.IMPROVE.SUCCESS',cost,waifu.name,waifu.level)
            except InsufficientTicketsError:
                await self.bot.respond(inter,'GACHA.IMPROVE.TOO_EXPENSIVE',cost)
                return
        except WaifuDNEError:
            await self.bot.respond(inter,'WAIFU.ERROR.NOT_IN_SERVER', waifuData)
            return
        