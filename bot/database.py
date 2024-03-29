from injections import WaifuData
from guilds import Server
import asyncpg as db
import qoi
import os, asyncio, logging
import yaml

IGNORE_DATABASE_ENVVAR='NO_DATABASE'
link = os.environ['DATABASE_URL']

enabled = True #allows others to query if they should make database requests
if link == IGNORE_DATABASE_ENVVAR:
    enabled = False

logger=logging.getLogger(os.environ['LOGGER_NAME'])

async def doCommandReturnAll(command:str,*args):
    if not enabled:
        return None
    conn:db.connection.Connection = await db.connect(link)
    result = await conn.fetch(command,*args)
    await conn.close()
    return result

async def doCommandReturn(command:str,*args):
    if not enabled:
        return None
    conn:db.connection.Connection = await db.connect(link)
    result = await conn.fetchrow(command,*args)
    await conn.close()
    return result

async def doCommand(command:str,*args):
    if not enabled:
        return None
    conn:db.connection.Connection = await db.connect(link)
    await conn.execute(command,*args)
    await conn.close()

async def createTables():
    cmdStrings=(
        "CREATE TABLE IF NOT EXISTS guilds(id BIGINT PRIMARY KEY, yaml TEXT)", 
        "CREATE TABLE IF NOT EXISTS waifus(name TEXT, source TEXT, data BYTEA, hash BIGINT UNIQUE)",
        "CREATE TABLE IF NOT EXISTS approvals(hash BIGINT PRIMARY KEY, data BYTEA, name TEXT, source TEXT)"
    )
    for cmdString in cmdStrings:
        await doCommand(cmdString)

async def getGuild(guildId:int) -> Server:
    cmdString="SELECT yaml FROM guilds WHERE id =$1"
    stored_server = await doCommandReturn(cmdString,guildId)
    return Server.buildFromDict(yaml.safe_load(stored_server.get('yaml')))

async def storeGuild(guild:Server):
    cmdString = """INSERT INTO guilds (id, yaml) VALUES ($1 ,$2)
    ON CONFLICT (id) DO UPDATE
    SET yaml = excluded.yaml
    """
    yaml_string=yaml.safe_dump(guild.getStorageDict())
    await doCommand(cmdString,guild.identity,yaml_string)

async def removeGuild(guildId:int):
    cmdString = "DELETE FROM guilds WHERE id = $1"
    await doCommand(cmdString,guildId)

async def storeWaifu(waifuData:WaifuData,image,imageHash:int):
    cmdString = "INSERT INTO waifus (name,source,data,hash) VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING"
    data = qoi.encode(image)
    await doCommand(cmdString,waifuData.name,waifuData.source,data,imageHash)

async def storeWaifuFile(waifuData:WaifuData,imagePath:str,imageHash:int):
    await storeWaifu(waifuData,qoi.read(imagePath),imageHash)

async def loadWaifu(imageHash:int):
    cmdString = "SELECT data FROM waifus WHERE hash = $1"
    image = await doCommandReturn(cmdString,imageHash)
    return qoi.decode(image.get('data'))

async def removeWaifu(imageHash:int):
    cmdString = "DELETE FROM waifus WHERE hash = $1 RETURNING name, source"
    data = await doCommandReturn(cmdString, imageHash)
    return WaifuData(data.get('name'),data.get('source'))

async def getWaifuHashes(waifuData:WaifuData):
    cmdString = "SELECT hash FROM waifus WHERE name = $1 AND source = $2"
    waifuHashes=await doCommandReturnAll(cmdString,waifuData.name,waifuData.source)
    return [waifuHash.get('hash') for waifuHash in waifuHashes]

async def getAllWaifus():
    cmdString = "SELECT name,source FROM waifus"
    allData = await doCommandReturnAll(cmdString)
    return [WaifuData(datum.get('name'),datum.get('source')) for datum in allData]

async def getAllGuilds():
    cmdString = "SELECT id FROM guilds"
    allData = await doCommandReturnAll(cmdString)
    return [datum.get('id') for datum in allData]

async def addApproval(id:int,image,waifuData:WaifuData):
    cmdString = "INSERT INTO approvals (hash, data, name, source) VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING"
    await doCommand(cmdString,id,qoi.encode(image),waifuData.name,waifuData.source)

async def removeApproval(id:int) -> tuple[bytes,WaifuData] :
    cmdString="DELETE FROM approvals WHERE hash = $1 RETURNING data, name, source"
    data = await doCommandReturn(cmdString,id)
    return (qoi.decode(data.get('data')),WaifuData(data.get('name'),data.get('source')))

async def getApproval(id:int) -> WaifuData:
    cmdString="SELECT name, source FROM approvals WHERE hash = $1"
    data = await doCommandReturn(cmdString,id)
    return WaifuData(data.get('name'),data.get('source'))

async def modifyApproval(id:int,newWaifuData:WaifuData) -> None:
    cmdString="UPDATE approvals SET name = $2, source = $3 WHERE hash = $1"
    await doCommand(cmdString,id,newWaifuData.name,newWaifuData.source)

asyncio.get_event_loop().run_until_complete(createTables()) #block until we ensure all tables are created