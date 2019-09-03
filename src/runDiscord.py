# Run the bot as a discord client
import random
import discord
import os
import evebot
import apikeys
import config
import logging
from string import Template
from models import Service, Server, Chat, User, Session, get_or_create
from helpers import commandHelpers
import asyncio

logger = logging.getLogger(__name__)

logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)

# Only log debug messages in debug mode
if (config.DEBUG):
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s %(levelname)-8s %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S')
else:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S')

class DiscordClient(discord.Client):
    def __init__(self):
        self.eve = None
        super().__init__()

    # Sets up the bot and makes sure it knows who it is.
    async def on_ready(self):
        logger.info('Logged in as')
        logger.info(client.user.name)
        logger.info(client.user.id)
        logger.info('------')

        session = Session()
        session.expire_on_commit = False
        self.service = get_or_create(session, Service, name="discord")
        database_user = get_or_create(session, User, id=client.user.id, service_id=self.service.id)
        database_user.username = client.user.display_name
        
        try:
            session.commit()
        except:
            logger.error("Couldn't commit bot user to database!")
            session.rollback()
        finally:
            session.close()

        self.eve = evebot.EveBot(database_user)

    # Processes messages by checking for commands and reactions
    async def on_message(self, message):

        # runs only on debug channels if debug is enabled.
        if config.DEBUG:
            if message.channel.id not in config.debug_channel_ids:
                return
        
        # other bots are unworthy of our attention
        if message.author.bot == True:
            return

        # if someone trying to run a command is not authorised, return
        if(commandHelpers.is_command(message.content) and not hasApprovedRole(message.author)):
            return

        # Processes messages from commands and handles errors.
        async def sendReply(text, edit=False, append=False, delete_after=None, **kwargs):
            # Attempts to send a message up to MAX_RETRY times because sometimes discord is rubbish
            MAX_RETRY = 3
            
            async def attempt(count=0):
                if(count < MAX_RETRY):
                    try:
                        if(edit):
                            return await edit.edit(text)
                        elif(append):
                            return await append.edit(message.content + text)

                        return await message.channel.send(text)
                    except discord.HTTPException as e:
                        logger.warning("Failed to send or edit message. " + str(e))
                        return await attempt(count + 1)
                    except discord.Forbidden as e:
                        logger.error("Cannot send message - permission forbidden! " + str(e))
                
                return None

            if text != "":
                del_message = await attempt()
                
                if(delete_after is not None and del_message is not None):
                    await asyncio.sleep(delete_after)
                    await del_message.delete()
                    return None
                return del_message
            return None

        if(self.eve):
            metadata = await self.constructMetadata(message)
            if(metadata is None):
                return

            # Actually process the message
            try:
                await self.eve.read(message.content, metadata, sendReply)
            except Exception as e:
                logger.error("Error reading message: " + str(e))

    async def on_message_delete(self, message):
        
        # runs only on debug channels if debug is enabled.
        if config.DEBUG:
            if message.channel.id not in config.debug_channel_ids:
                return
        
        # Don't trigger this when bot messages are deleted
        if(message.author.id == client.user.id):
            return
        
        log_channel_id = config.log_channels.get(message.guild.id)
        log_channel = discord.utils.get(message.guild.text_channels, id=log_channel_id)
        embed = discord.Embed(title="Message Deleted",
                              type="rich",
                              description=Template("A message from $author was deleted from #$channel").substitute(
                                  author=message.author.name,
                                  channel=message.channel.name),
                              colour=0xff0000)

        if(message.content == ""):
            message.content = "None"

        embed.add_field(name="User", value = "<@" + str(message.author.id) + ">", inline=False)
        embed.add_field(name="ID", value = str(message.author.id), inline=False)
        embed.add_field(name="Timestamp", value = str(message.created_at), inline = False)
        embed.add_field(name="Channel", value = "<#"+str(message.channel.id)+">", inline=False)
        embed.add_field(name="Content", value = message.content, inline=False)
        
        if(len(message.attachments) > 0):
            for attachment in message.attachments:
                embed.add_field(name="Attachment", value=attachment.proxy_url + "\n", inline=False)
        
        try:
            await log_channel.send(embed=embed)
        except discord.HTTPException as e:
            logger.error("Could not log deleted message. " + str(e))
        except discord.Forbidden as e:
            logger.error("Do not have permissions to log deleted message. " + str(e))

    async def on_message_edit(self, before, after):

        # runs only on debug channels if debug is enabled.
        if config.DEBUG:
            if before.channel.id not in config.debug_channel_ids:
                return

        # Don't trigger this when bot messages are edited to avoid loops
        if(before.author.id == client.user.id):
            return

        # Work around for weird behaviour where the edit event gets called twice (the second time with blank message content)
        if(before.content == "" and after.content == ""):
            before.content = "None"
            after.content = "None"

        # Work around for weird behaviour where the edit event gets called after discord updates link previews
        if(before.content == after.content):
            return
        
        log_channel_id = config.log_channels.get(before.guild.id)
        log_channel = discord.utils.get(before.guild.text_channels, id=log_channel_id)
        embed = discord.Embed(title="Message Edited", 
                              type="rich",
                              description=Template("A message from $author was edited in #$channel").substitute(
                                  author=before.author.name,
                                  channel=before.channel.name),
                              colour=0xffff00)

        embed.add_field(name="User", value = "<@" + str(before.author.id) + ">", inline = False)
        embed.add_field(name="ID", value = str(before.author.id), inline = False)
        embed.add_field(name="Channel", value = "<#"+str(before.channel.id)+">", inline = False)
        embed.add_field(name="Original message", value = str(before.content), inline = False)
        embed.add_field(name="Original date", value = str(before.created_at), inline = False)
        embed.add_field(name="Edited Message", value = after.content, inline = False)
        embed.add_field(name="Edited date", value = str(after.created_at), inline = False)
        
        try:
            await log_channel.send(embed=embed)
        except discord.HTTPException as e:
            logger.error("Could not log edited message. " + str(e))
        except discord.Forbidden as e:
            logger.error("Do not have permissions to log edited message. " + str(e))


    async def on_raw_reaction_add(self, event):
        await self.do_raw_reactions(event, "REACTION_ADD")
        
    async def on_raw_reaction_remove(self, event):
        await self.do_raw_reactions(event, "REACTION_REMOVE")

    async def do_raw_reactions(self, event, event_type):
        channel = self.get_channel(event.channel_id)

        if(channel is None):
            return
    
        try:
            message = await channel.fetch_message(event.message_id)
        except (NotFound, Forbidden, HTTPException) as e:
            logger.error("Error processing reaction_add: " + str(e))
            return
            
        guild = self.get_guild(event.guild_id)
        if(guild == None): 
            return
        
        user = self.get_user(event.user_id)
        if(user == None):
            return
        
        # other bots are unworthy of our attention
        if user.bot == True:
            return

        # runs only on debug channels if debug is enabled.
        if config.DEBUG:
            if message.channel.id not in config.debug_channel_ids:
                return

        if(self.eve):
            
            metadata = await self.constructMetadata(message)
            if(metadata is None):
                return

            metadata["user"] = user
            metadata["event"] = event

            # Actually process the message
            try:
                await self.eve.doTagReacts(event_type, metadata)
            except Exception as e:
                logger.error("Error processing tag reaction: " + str(e))


    async def constructMetadata(self, message):
        try:
            session = Session()
            session.expire_on_commit = False

            if(message.guild):
                current_server = Server(id=message.guild.id, service_id=self.service.id, server_name=message.guild.name)
            else:
                current_server = None

            current_user = User(id=message.author.id, service_id=self.service.id, username=message.author.display_name)

            if(message.channel.name):
                current_channel = Chat(id=message.channel.id, server_id=current_server.id, chat_name=message.channel.name, nsfw=message.channel.is_nsfw())
            else:
                current_channel = get_or_create(session, Chat, id=message.channel.id, server_id=current_server.id, chat_name=message.channel.id)

        except Exception as e:
            logger.error("Couldn't get data from message! " + str(e))
            return None
        
        # Metadata for use by commands and reactions
        metadata = {"service": self.service, "user":current_user, "server":current_server, "chat":current_channel, "message":message, "client":self}
        return metadata

def hasApprovedRole(discordUser):
    for role in discordUser.roles:
        if role.id in config.approved_roles.get(discordUser.guild.id, []):
            return True

    return False

if (__name__ == "__main__"):
    client = DiscordClient()
    client.run(apikeys.discordkey)
