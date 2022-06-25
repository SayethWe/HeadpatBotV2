from attr import s
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

class WaifuData:
    def __init__(self,folderStructure:str):
        self._name=folderStructure.split('/')[1]
        self._source=folderStructure.split('/')[1]

    @property
    def name(self):
        return self._name.title()

    @property
    def source(self):
        return self._source.title()

    def __repr__(self):
        return f'{self.name}|{self.source}'

@dataclass
class NameSourceWaifu:
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
async def getWaifu(
    waifu:str=commands.Param(autocomplete=waifu_autocomplete,description="Waifu in source/name form")
) -> WaifuData:
    return WaifuData(waifu.split('/')[1].title(),waifu.split('/')[0].title())

@commands.register_injection
async def twoFieldWaifu(
    inter:ApplicationCommandInteraction,
    name:str=commands.Param(autocomplete=name_autocomplete,description="Name of waifu"),
    source:str=commands.Param(autocomplete=source_autocomplete,description="Origin of Waifu")
) -> NameSourceWaifu:
    return NameSourceWaifu(name,source)
