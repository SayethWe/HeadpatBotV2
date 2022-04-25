from guilds import Server
import psycopg2 as db
import qoi
import os, pickle

IGNORE_DATABASE_ENVVAR='NO_DATABASE'
link = os.environ['DATABASE_URL']

enabled = True #allows others to query if they should make database requests
if link == IGNORE_DATABASE_ENVVAR:
    enabled = False


#connection = db.connect(database="postgres",user="postgres",host="127.0.0.1",port="5432")
def doCommandReturnAll(command:str,*args):
    if not enabled:
        return None
    conn = db.connect(link)
    cur = conn.cursor()
    execStr = command.format(*args)
    #print(execStr)
    cur.execute(execStr)
    conn.commit()
    result = cur.fetchall()
    result = [subres[0] for subres in result]
    cur.close()
    conn.close()
    return result

def doCommandReturn(command:str,*args):
    if not enabled:
        return None
    conn = db.connect(link)
    cur = conn.cursor()
    execStr = command.format(*args)
    #print(execStr)
    cur.execute(execStr)
    conn.commit()
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result

def doCommand(command:str,*args):
    if not enabled:
        return None
    conn = db.connect(link)
    cur = conn.cursor()
    execStr = command.format(*args)
    #print(execStr)
    cur.execute(execStr)
    conn.commit()
    cur.close()
    conn.close()

def createTables():
    cmdStrings=(
        "CREATE TABLE IF NOT EXISTS guilds(id BIGINT PRIMARY KEY, data BYTEA)", 
        "CREATE TABLE IF NOT EXISTS waifus(name TEXT, source TEXT, data BYTEA, hash BIGINT UNIQUE)"
    )
    for cmdString in cmdStrings:
        doCommand(cmdString)

def getGuildPickle(guildId:int) -> Server:
    cmdString="SELECT data FROM guilds WHERE id ={0}"
    pickle_string = doCommandReturn(cmdString,guildId)
    return pickle.loads(pickle_string.tobytes())

def storeGuildPickle(guild:Server):
    cmdString = """INSERT INTO guilds (id, data) VALUES ({0},{1})
    ON CONFLICT (id) DO UPDATE
    SET data = excluded.data
    """
    pickle_bytes = pickle.dumps(guild)
    doCommand(cmdString,guild.identity,db.Binary(pickle_bytes))

def storeWaifu(name:str,source:str,image,imageHash:int):
    cmdString = "INSERT INTO waifus (name,source,data,hash) VALUES ('{0}','{1}',{2},{3}) ON CONFLICT DO NOTHING"
    data = qoi.encode(image)
    doCommand(cmdString,name,source,db.Binary(data),imageHash)

def storeWaifuFile(name:str,source:str,imagePath:str,imageHash:int):
    storeWaifu(name,source,qoi.read(imagePath),imageHash)

def loadWaifu(imageHash:int):
    cmdString = "SELECT data FROM waifus WHERE hash = '{0}'"
    image = doCommandReturn(cmdString,imageHash)
    return qoi.decode(image.tobytes())

def getWaifuHashes(name:str,source:str):
    cmdString = "SELECT hash FROM waifus WHERE name = '{0}' AND source = '{1}'"
    return doCommandReturnAll(cmdString,name,source)

def getAllWaifus():
    cmdString = "SELECT (name,source) FROM waifus"
    allData = doCommandReturnAll(cmdString)
    return [(datum.split(',')[0][1:].replace('"',''),datum.split(',')[1][:-1].replace('"','')) for datum in allData]

def getAllGuilds():
    cmdString = "SELECT id FROM guilds"
    allData = doCommandReturnAll(cmdString)
    return allData

createTables()