from disnake import ApplicationCommandInteraction
import os, glob
from headpatExceptions import WaifuDNEError
from disnake.ext import commands
from dataclasses import dataclass

POLL_FOLDER=os.path.join('img','waifu')
HEADPAT_FOLDER=os.path.join('img','headpat')

async def source_autocomplete(
    inter:ApplicationCommandInteraction,
    input:str
):
    raw_list = glob.glob('*/*/',root_dir=POLL_FOLDER)
    valid = sorted(set([source.split('/')[0] for source in raw_list if input.title() in source]))
    return valid[:25] #discord can take 25 options

async def name_autocomplete(
    inter:ApplicationCommandInteraction,
    input:str
):
    raw_list = glob.glob('*/*/',root_dir=POLL_FOLDER)
    valid = sorted(set([source.split('/')[1] for source in raw_list if input.title() in source]))
    return valid[:25]

async def waifu_autocomplete(
    inter:ApplicationCommandInteraction,
    input:str
):
    raw_list = glob.glob('*/*',root_dir=POLL_FOLDER)
    valid = sorted(set([source for source in raw_list if input.title() in source]))
    return valid[:25]

async def gacha_autocomplete(
    inter:ApplicationCommandInteraction,
    input:str
):
    rawList = [f'{waifu.source}/{waifu.name}' for waifu in inter.bot.servers[inter.guild.id].claimedWaifus(inter.author.id)]
    valid = sorted(set([waifuFolder for waifuFolder in rawList if input.title() in waifuFolder]))
    return valid[:25]

async def pull_autocomplete(
    inter:ApplicationCommandInteraction,
    input:str
):
    raw_list = glob.glob('*/*',root_dir=POLL_FOLDER)
    valid=[]
    for waifu in raw_list:
        if input.title() in waifu:
            try:
                inter.bot.servers[inter.guild.id].getWaifuByNameSource(waifu.split('/')[1],waifu.split('/')[0])
            except WaifuDNEError: 
                valid.append(waifu)
    valid = sorted(valid)
    return valid[:25]

async def server_autocomplete(
     inter:ApplicationCommandInteraction,
    input:str
):
    rawList = [f'{waifu.source}/{waifu.name}' for waifu in inter.bot.servers[inter.guild.id].waifus]
    valid = sorted(set([waifuFolder for waifuFolder in rawList if input.title() in waifuFolder]))
    return valid[:25]

@dataclass
class WaifuData:
    _name:str
    _source: str

    @property
    def name(self):
        return self._name.title()

    @property
    def source(self):
        return self._source.title()

    def __repr__(self):
        return f'{self.name}|{self.source}'

@commands.register_injection
async def folderWaifu(
    waifu:str=commands.Param(autocomplete=waifu_autocomplete,description="Waifu in source/name form")
) -> WaifuData:
    return WaifuData(waifu.split('/')[1],waifu.split('/')[0])

@commands.register_injection
async def nameSourceWaifu(
    name:str=commands.Param(autocomplete=name_autocomplete,description="Name of waifu"),
    source:str=commands.Param(autocomplete=source_autocomplete,description="Origin of Waifu")
) -> WaifuData:
    return WaifuData(name,source)

@commands.register_injection
async def gachaWaifu(
    waifu:str=commands.Param(autocomplete=gacha_autocomplete,description="Claimed Waifu in source/name form")
) -> WaifuData:
    return await folderWaifu(waifu)

@commands.register_injection
async def missingWaifu(
    waifu:str=commands.Param(autocomplete=pull_autocomplete,description="Waifu not in server in source/name form")
) -> WaifuData:
    return await folderWaifu(waifu)

@commands.register_injection
async def serverWaifu(
    waifu:str=commands.Param(autocomplete=server_autocomplete,description="Waifu in server in source/name form")
) -> WaifuData:
    return await folderWaifu(waifu)