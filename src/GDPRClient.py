import datetime
import discord
import apikeys
import logging
import config 
import time
from discord import ChannelType
import os
from helpers import managementHelpers


class GDPRClient(discord.Client):

    async def on_ready(self):
        self.logger = logging.getLogger(__name__)

        # Only log debug messages in debug mode
        if (config.DEBUG):
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    async def getGDPR(self, userid, guildid, sendReply):
        guild = self.get_guild(guildid)
        user = self.get_user(int(userid))

        if(guild is None):
            return await sendReply("Could not determine guild")

        if(user is None):
            return await sendReply("Could not find user with id: " + userid)

        filename = "gdprdata/data.txt"
        mymessage = await sendReply("Compiling GDPR data...")

        with open(filename, 'w') as f:
            for channel in guild.channels:
                try:
                    if channel.type == ChannelType.text:
                        await sendReply("Processing data for: " + str(channel), edit=mymessage)
                        async for message in channel.history(limit=None):
                            if isGDPRableMessage(message, userid):
                                f.write(managementHelpers.messageToString(message))
                except Exception as e:
                    await sendReply("Exception while processing channel: " + str(channel))
                    self.logger.error(e)
                    pass
        
        await sendReply("GDPR Data Compiled!", edit=mymessage)
        filesize = os.path.getsize(filename)

        if(filesize < 8*1000*1000):
            await sendReply("Data: ", file=filename)
        else:
            await sendReply("Data is too large ("+str(filesize)+" megabytes) to send via discord! :(")


    async def deleteGDPR(self, userid, guildid, sendReply):
        guild = self.get_guild(guildid)
        user = self.get_user(int(userid))

        if(guild is None):
            return await sendReply("Could not determine guild")

        if(user is None):
            return await sendReply("Could not find user with id: " + userid)

        mymessage = await sendReply("Deleting messages sent by "+userid+" in compliance with gdpr.")

        for channel in guild.channels:
            try:
                if channel.type == ChannelType.text:
                    await sendReply("Processing data for: " + str(channel), edit=mymessage)
                    await managementHelpers.clearChannelOfUser(channel, userid)
            except Exception as e:
                await sendReply("Exception while processing channel: " + str(channel))
                self.logger.error(e)
                pass
        
        await sendReply("Data for user " + str(userid) + " deleted!", edit=mymessage)

def isGDPRableMessage(message, userid):
    for user in message.mentions:
        if(str(user.id) == str(userid)):
            return True
    return managementHelpers.userPostedMessage(message, userid)
