from disnake import ApplicationCommandInteraction
import glob
import images
from disnake.ext import commands
from dataclasses import dataclass

async def source_autocomplete(
    inter:ApplicationCommandInteraction,
    input:str
):
    raw_list = glob.glob('*/*/',root_dir=images.POLL_FOLDER)
    valid = sorted(set([source.split('/')[0] for source in raw_list if input.title() in source]))
    return valid[:25] #discord can take 25 options

async def name_autocomplete(
    inter:ApplicationCommandInteraction,
    input:str
):
    raw_list = glob.glob('*/*/',root_dir=images.POLL_FOLDER)
    valid = sorted(set([source.split('/')[1] for source in raw_list if input.title() in source]))
    return valid[:25]

async def waifu_autocomplete(
    inter:ApplicationCommandInteraction,
    input:str
):
    raw_list = glob.glob('*/*',root_dir=images.POLL_FOLDER)
    valid = sorted(set([source for source in raw_list if input.title() in source]))
    return valid[:25]

@dataclass
class WaifuData:
    name:str
    source: str

    def __repr__(self):
        return f'{self.name}|{self.source}'

@commands.register_injection
async def getWaifu(
    inter:ApplicationCommandInteraction,
#    name:str=commands.Param(autocomplete=name_autocomplete,description="Name of waifu"),
#    source:str=commands.Param(autocomplete=source_autocomplete,description="Origin of Waifu")
    waifu:str=commands.Param(autocomplete=waifu_autocomplete,description="Waifu in source/name form")
) -> WaifuData:
    return WaifuData(waifu.split('/')[1].title(),waifu.split('/')[0].title())