import os, sys, logging, traceback
from discord_webhook_logging import DiscordWebhookHandler

os.environ['LOGGER_NAME']='disnake'

#get the logger
logger = logging.getLogger(os.environ['LOGGER_NAME'])
logger.setLevel(logging.DEBUG)
format=logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

#debug file handler
fhandler = logging.FileHandler(filename='discord.log', encoding = 'utf-8', mode = 'w')
fhandler.setLevel('DEBUG')
fhandler.setFormatter(format)
logger.addHandler(fhandler)

#info console handler
chandler = logging.StreamHandler(stream = sys.stdout)
chandler.setFormatter(format)
chandler.setLevel('INFO')
logger.addHandler(chandler)

#warning webhook handler, if a link exists
if 'LOGS_HOOK' in os.environ:
    whandler = DiscordWebhookHandler(webhook_url=os.environ['LOGS_HOOK'])
    whandler.setLevel('WARNING')
    logger.addHandler(whandler)

#use logger on uncaught exceptions
def log_uncaught_exceptions(type, value, trace):
    for line in traceback.TracebackException(type,value,trace).format(chain=True):
        logger.exception(line)
    logging.exception(value)

    sys.__excepthook__(type, value, trace) #call the default too

sys.excepthook = log_uncaught_exceptions #override default hook to use the logger

from headpatBot import HeadpatBot
from cogs.pollCog import PollCog
from cogs.utilityCogs import TimerCog, TestCog, HelpCog
from cogs.managementCogs import ManageWaifusCog, ServerOptionsCog
from cogs.waifuCogs import WaifuCog, GachaCog

#set up the bot
if 'TEST_ENV' in os.environ:
    #development version
    bot=HeadpatBot(
        test_guilds=[int(g) for g in os.environ['TEST_ENV'].split(",")]
    )
else:
     bot=HeadpatBot(    )

#register the cogs
bot.add_cog(HelpCog(bot))
bot.add_cog(TimerCog(bot))
bot.add_cog(PollCog(bot))
bot.add_cog(ManageWaifusCog(bot))
bot.add_cog(WaifuCog(bot))
bot.add_cog(GachaCog(bot))
bot.add_cog(ServerOptionsCog(bot))
if 'TEST_ENV' in os.environ:
    #devopment commands
    bot.add_cog(TestCog(bot))

#run the bot
TOKEN=os.environ['DISCORD_TOKEN']
bot.run(TOKEN)