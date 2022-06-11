import logging, os
import yaml
from numpy.random import default_rng
from glom import glom

logger = logging.getLogger(os.environ['LOGGER_NAME'])

with open(os.path.join("bot","responses.yaml"),"r") as file:
    try:
        responses = yaml.safe_load(file)
    except yaml.YAMLError as err:
        logger.error(err)

rng = default_rng()

def getResponse(request:str, *args : str) -> str:
    request=request.upper()
    replies = glom(responses,request)
    reply = rng.choice(replies)
    return reply.replace('[NEWLINE]','\n').format(*args)