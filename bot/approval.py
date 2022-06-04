# Copyright (C) 2022 geekman9097
# 
# This file is part of HeadpatBot.
# 
# HeadpatBot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# HeadpatBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with HeadpatBot.  If not, see <http://www.gnu.org/licenses/>.

import os
from io import BytesIO
from disnake.ui import View, Button, TextInput, Modal
from disnake import Attachment, ButtonStyle
from disnake.ext.commands import Bot
import images, responder

approval_channel=int(os.environ['OWNER_CHANNEL'])
announce_channel=int(os.environ['SHARE_CHANNEL'])

async def getWaifuApproval(bot: Bot, image: Attachment, name:str,source:str):
     
    async def accept_callback(button_inter):
        #print('accept')
        lockButtons()
        imageBytes = BytesIO(await image.read())
        existingWaifu = images.savePollImage(imageBytes,hash(image),os.path.join(source,name))
        announce=bot.get_channel(announce_channel)
        if announce is None:
            announce = bot.fetch_channel(announce_channel)
        await button_inter.send(responder.getResponse('WAIFU.ADD.APPROVE',name))
        attachment = await image.to_file()
        if existingWaifu:
            await announce.send(responder.getResponse('WAIFU.ADD.ANNOUNCE.EXISTING',name,source),file = attachment)
        else:
            await announce.send(responder.getResponse('WAIFU.ADD.ANNOUNCE.NEW',name,source),file = attachment)


    async def edit_callback(button_inter):
        #create modal
        #send modal
        #edit fields
        pass

    async def reject_callback(button_inter):
        #print('reject')
        lockButtons()
        await button_inter.send(responder.getResponse('WAIFU.ADD.DENY',name))

    view=View(timeout=None)
    acceptButton=Button(label='accept',style=ButtonStyle.green)
    #editButton=Button(label='edit',style=ButtonStyle.blurple)
    rejectButton=Button(label='reject',style=ButtonStyle.red)
    acceptButton.callback=accept_callback
    rejectButton.callback=reject_callback
    view.add_item(acceptButton)
    view.add_item(rejectButton)

    def lockButtons():
        acceptButton.disabled = True
        #editButton.disabled = True
        rejectButton.disabled = True

    request_channel = bot.get_channel(approval_channel)
    attachment = await image.to_file()
    await request_channel.send(responder.getResponse('WAIFU.ADD.ASK',name,source),
        view=view,file=attachment)

class EditModal(Modal):
    def __init__(self,name,source):
        components=[
            TextInput(label='name',custom_id='name edit',value=name),
            TextInput(label='source',custom_id='source edit',value=source)
        ]
        super.__init__(title='Edit Waifu Details',custom_id='waifu_edit',
            components=components)
    
    async def callback(self, inter):
        pass
