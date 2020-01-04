import logging
import asyncio
import config

logger = logging.getLogger(__name__)

# Only log debug messages in debug mode
if (config.DEBUG):
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

async def clearChannel(channel):
    message_list = []
    messg_count = 0

    async for message in channel.history(limit=None):
        message_list.append(message)
        messg_count += 1
        
        if len(message_list) == 99:
            await doBulkDelete(message_list, channel)
            message_list = []

    await doBulkDelete(message_list, channel)

async def clearChannelOfUser(channel, userid):
    message_list = []
    messg_count = 0

    async for message in channel.history(limit=None):
        if(userPostedMessage(message,userid)):
            message_list.append(message)
            messg_count += 1
            
            if len(message_list) == 99:
                await doBulkDelete(message_list, channel)
                message_list = []

    await doBulkDelete(message_list, channel)


async def bulkDeleteAll(messages, channel):
    message_list = []
    messg_count = 0

    for message in messages:
        message_list.append(message)
        messg_count += 1
        
        if len(message_list) == 99:
            await doBulkDelete(message_list, channel)
            message_list = []

    await doBulkDelete(message_list, channel)

async def doBulkDelete(message_list, channel):
    try:
        await channel.delete_messages(message_list)
        await asyncio.sleep(1.5)
    except Exception as e:
        logger.error("Error bulk deleting messages: " + str(e))
        await asyncio.sleep(1.5)
        await doBulkDeleteOneAtATime(message_list)

async def doBulkDeleteOneAtATime(message_list):
    logger.info("Deleting messages one at a time, this will take a while")
    try:
        for message in message_list:
            await message.delete()
            await asyncio.sleep(1.5)
    except Exception as e:
        logger.error("Error deleting message: " + str(e))
        
def userPostedMessage(message, userid):
    return str(message.author.id) == str(userid)

def messageToString(message):
    basestring = "Author: " + str(message.author.id) + "\n" + \
            "Server: " + str(message.guild.name) + "\n" + \
            "Channel: "+ str(message.channel.name) + "\n" + \
            "Message: " + str(message.content)

    attachments = "" if len(message.attachments) == 0 else "\nAttachments: " + str(message.attachments)
    terminator = "\n---------------------------------------\n"

    return basestring + attachments + terminator
