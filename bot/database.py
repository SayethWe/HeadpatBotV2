from guilds import Server
import asyncpg as db
import qoi
import os, pickle, asyncio

IGNORE_DATABASE_ENVVAR='NO_DATABASE'
link = os.environ['DATABASE_URL']

enabled = True #allows others to query if they should make database requests
if link == IGNORE_DATABASE_ENVVAR:
    enabled = False


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
        "CREATE TABLE IF NOT EXISTS guilds(id BIGINT PRIMARY KEY, data BYTEA)", 
        "CREATE TABLE IF NOT EXISTS waifus(name TEXT, source TEXT, data BYTEA, hash BIGINT UNIQUE)"
    )
    for cmdString in cmdStrings:
        await doCommand(cmdString)

async def getGuildPickle(guildId:int) -> Server:
    cmdString="SELECT data FROM guilds WHERE id =$1"
    pickle_string = await doCommandReturn(cmdString,guildId)
    return pickle.loads(pickle_string.get('data'))

async def storeGuildPickle(guild:Server):
    cmdString = """INSERT INTO guilds (id, data) VALUES ($1 ,$2)
    ON CONFLICT (id) DO UPDATE
    SET data = excluded.data
    """
    pickle_bytes = pickle.dumps(guild)
    await doCommand(cmdString,guild.identity,pickle_bytes)

async def storeWaifu(name:str,source:str,image,imageHash:int):
    cmdString = "INSERT INTO waifus (name,source,data,hash) VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING"
    data = qoi.encode(image)
    await doCommand(cmdString,name,source,data,imageHash)

async def storeWaifuFile(name:str,source:str,imagePath:str,imageHash:int):
    await storeWaifu(name,source,qoi.read(imagePath),imageHash)

async def loadWaifu(imageHash:int):
    cmdString = "SELECT data FROM waifus WHERE hash = $1"
    image = await doCommandReturn(cmdString,imageHash)
    return qoi.decode(image.get('data'))

async def getWaifuHashes(name:str,source:str):
    cmdString = "SELECT hash FROM waifus WHERE name = $1 AND source = $2"
    waifuHashes=await doCommandReturnAll(cmdString,name,source)
    return [waifuHash.get('hash') for waifuHash in waifuHashes]

async def getAllWaifus():
    cmdString = "SELECT name,source FROM waifus"
    allData = await doCommandReturnAll(cmdString)
    return [(datum.get('name'),datum.get('source')) for datum in allData]

async def getAllGuilds():
    cmdString = "SELECT id FROM guilds"
    allData = await doCommandReturnAll(cmdString)
    return [datum.get('id') for datum in allData]

asyncio.get_event_loop().run_until_complete(createTables())