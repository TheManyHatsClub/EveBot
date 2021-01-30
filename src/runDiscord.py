# Run the bot as a discord client
import logging

import discord

import apikeys
import config
import evebot
from helpers import commandHelpers, discordHelpers
from models import Service, Server, Chat, User, Session, get_or_create

logger = logging.getLogger(__name__)

logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)

# Only log debug messages in debug mode
if config.DEBUG:
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s %(levelname)-8s %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S')
else:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S')


class DiscordClient(discord.Client):
    def __init__(self, **kwargs):
        self.eve = None
        self.service = None
        super().__init__(**kwargs)

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

        if not discordHelpers.shouldProcessMessage(message):
            return

        # if someone trying to run a command is not authorised, return
        if commandHelpers.is_command(message.content) and not discordHelpers.hasApprovedRole(message.author):
            return

        if self.eve:
            metadata = await self.construct_metadata(message)
            if metadata is None:
                return

            sendReply = discordHelpers.buildSendReply(message)

            # Actually process the message
            try:
                await self.eve.read(message.content, metadata, sendReply)
            except Exception as e:
                logger.error("Error reading message: " + str(e))

    async def on_message_delete(self, message):

        if not discordHelpers.shouldProcessMessage(message):
            return

        log_channel_id = config.log_channels.get(message.guild.id)
        log_channel = discord.utils.get(message.guild.text_channels, id=log_channel_id)

        embed = discordHelpers.buildOnDeleteLogEmbed(message)
        
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden as e:
            logger.error("Do not have permissions to log deleted message. " + str(e))
        except discord.HTTPException as e:
            logger.error("Could not log deleted message. " + str(e))

    async def on_message_edit(self, before, after):

        if not discordHelpers.shouldProcessMessage(before):
            return

        # Work around for weird behaviour where the edit event
        # gets called twice (the second time with blank message content)
        if before.content == "" and after.content == "":
            before.content = "None"
            after.content = "None"

        # Work around for weird behaviour where the edit event gets called after discord updates link previews
        if before.content == after.content:
            return
        
        log_channel_id = config.log_channels.get(before.guild.id)
        log_channel = discord.utils.get(before.guild.text_channels, id=log_channel_id)

        embed = discordHelpers.buildOnEditLogEmbed(before, after)
        
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden as e:
            logger.error("Do not have permissions to log edited message. " + str(e))
        except discord.HTTPException as e:
            logger.error("Could not log edited message. " + str(e))

    async def on_raw_reaction_add(self, event):
        await self.do_raw_reactions(event, "REACTION_ADD")
        
    async def on_raw_reaction_remove(self, event):
        await self.do_raw_reactions(event, "REACTION_REMOVE")

    async def do_raw_reactions(self, event, event_type):
        channel = self.get_channel(event.channel_id)
        if channel is None:
            return

        guild = self.get_guild(event.guild_id)
        if guild is None:
            return

        user = self.get_user(event.user_id)

        if user is None:
            return

        # other bots are unworthy of our attention
        if user.bot:
            return

        try:
            message = await channel.fetch_message(event.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            logger.error("Error processing reaction_add: " + str(e))
            return

        # runs only on debug channels if debug is enabled.
        if config.DEBUG and message.channel.id not in config.debug_channel_ids:
            return

        if self.eve:
            
            metadata = await self.construct_metadata(message)
            if metadata is None:
                return

            metadata["user"] = user
            metadata["event"] = event

            # Actually process the message
            try:
                await self.eve.do_tag_reacts(event_type, metadata)
            except Exception as e:
                logger.error("Error processing tag reaction: " + str(e))

    async def on_member_join(self, member):
        pass

    async def on_member_remove(self, member):
        pass

    async def construct_metadata(self, message):
        try:
            session = Session()
            session.expire_on_commit = False

            if message.guild:
                current_server = Server(id=message.guild.id, service_id=self.service.id, server_name=message.guild.name)
            else:
                current_server = None

            current_user = User(id=message.author.id, service_id=self.service.id, username=message.author.display_name)

            if message.channel.name:
                current_channel = Chat(id=message.channel.id, server_id=current_server.id, chat_name=message.channel.name, nsfw=message.channel.is_nsfw())
            else:
                current_channel = get_or_create(session, Chat, id=message.channel.id, server_id=current_server.id, chat_name=message.channel.id)

        except Exception as e:
            logger.error("Couldn't get data from message! " + str(e))
            return None
        
        # Metadata for use by commands and reactions
        metadata = {"service": self.service, "user":current_user, "server":current_server, "chat":current_channel, "message":message, "client":self}
        return metadata


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.members = True
    client = DiscordClient(intents=intents)
    client.run(apikeys.discordkey)
