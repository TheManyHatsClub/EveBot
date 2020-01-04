import datetime
import discord
import apikeys
import logging
import config 
import time

logger = logging.getLogger(__name__)

# Only log debug messages in debug mode
if (config.DEBUG):
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

class CleanupClient(discord.Client):
    async def on_ready(self):
        logger.info("Initiating log cleanup.")
        channel = self.get_channel(config.log_channels.get(config.servers.get("TMHC")))
        if(channel is None):
            logger.error("Unable to find log channel!")
        messg_count = 0 
        message_list = []

        async for message in channel.history(limit=None):
            if(datetime.datetime.now().timestamp() - message.created_at.timestamp() > 86400):
                message_list.append(message)
                messg_count += 1
            if len(message_list) == 99:
                try:
                    await channel.delete_messages(message_list)
                    time.sleep(1)
                except Exception as e:
                    logger.error(e)
                    for message in message_list:
                        await message.delete()
                        time.sleep(1)
                message_list = []
        try:
            await channel.delete_messages(message_list)
            time.sleep(1)
        except Exception as e:
            logger.error(e)
            for message in message_list:
                await message.delete()
                time.sleep(1)
        message_list = []

        logger.info(str(messg_count) + " messages deleted.")
        await self.close()

if(__name__ == "__main__"):
    client = CleanupClient()
    client.run(apikeys.workerkey)
