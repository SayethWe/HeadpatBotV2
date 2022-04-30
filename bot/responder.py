import os
import yaml
from numpy.random import default_rng
from glom import glom
import logging

logger = logging.getLogger('discord')

with open(os.path.join("bot","responses.yaml"),"r") as file:
    try:
        responses = yaml.safe_load(file)
    except yaml.YAMLError as err:
        logger.debug(err)

rng = default_rng()

def getResponse(request:str, *args : str) -> str:
    request=request.upper()
    replies = glom(responses,request)
    reply = rng.choice(replies)
    return reply.format(*args)