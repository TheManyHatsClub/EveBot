import discord
import string
import asyncio
import logging
import config

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


def buildOnDeleteLogEmbed(message):
    embed = discord.Embed(title="Message Deleted",
                          type="rich",
                          description=string.Template("A message from $author was deleted from #$channel").substitute(
                              author=message.author.name,
                              channel=message.channel.name),
                          colour=0xff0000)

    if (message.content == ""):
        message.content = "None"

    addContextToLogEmbed(embed, message.author.id, message.channel.id)
    addMessageToLogEmbed(embed, "Content", message.content, message.created_at, message.attachments)

    return embed


def buildOnEditLogEmbed(beforeMessage, afterMessage):
    embed = discord.Embed(title="Message Edited",
                          type="rich",
                          description=string.Template("A message from $author was edited in #$channel").substitute(
                              author=beforeMessage.author.name,
                              channel=beforeMessage.channel.name),
                          colour=0xffff00)

    addContextToLogEmbed(embed, beforeMessage.author.id, beforeMessage.channel.id)
    addMessageToLogEmbed(embed, "Original message", beforeMessage.content, beforeMessage.created_at, beforeMessage.attachments)
    addMessageToLogEmbed(embed, "Edited message", afterMessage.content, afterMessage.edited_at, afterMessage.attachments)

    return embed


def addContextToLogEmbed(embed, authorID, channelID):
    embed.add_field(name="User", value="<@" + str(authorID) + ">", inline=False)
    embed.add_field(name="ID", value=str(authorID), inline=False)
    embed.add_field(name="Channel", value="<#" + str(channelID) + ">", inline=False)


def addMessageToLogEmbed(embed, name, content, timestamp, attachments):
    embed.add_field(name=name, value=content, inline=False)
    embed.add_field(name="Timestamp", value=str(timestamp), inline=False)

    if (len(attachments) > 0):
        for attachment in attachments:
            embed.add_field(name="Attachment", value=attachment.proxy_url + "\n", inline=False)


# Processes messages from commands and handles errors.
def buildSendReply(message):
    async def sendReply(text, edit=False, append=False, delete_after=None, file=None, **kwargs):
        # Attempts to send a message up to MAX_RETRY times because sometimes discord is rubbish
        MAX_RETRY = 3

        async def attempt(count=0):
            if (count < MAX_RETRY):
                try:
                    if (edit):
                        return await edit.edit(content=text)
                    elif (append):
                        return await append.edit(content=message.content + text)
                    elif (file):
                        return await message.channel.send(text, file=discord.File(file))

                    return await message.channel.send(text)
                except discord.Forbidden as e:
                    logger.error("Cannot send message - permission forbidden! " + str(e))
                except discord.HTTPException as e:
                    logger.warning("Failed to send or edit message. " + str(e))
                    return await attempt(count + 1)

            return None

        if text != "":
            del_message = await attempt()

            if (delete_after is not None and del_message is not None):
                await asyncio.sleep(delete_after)
                await del_message.delete()
                return None
            return del_message
        return None

    return sendReply

def hasApprovedRole(discordUser):
    for role in discordUser.roles:
        if role.id in config.approved_roles.get(discordUser.guild.id, []):
            return True

    return False

def shouldProcessMessage(message):
    # runs only on debug channels if debug is enabled.
    if config.DEBUG and message.channel.id not in config.debug_channel_ids:
            return False

    # other bots are unworthy of our attention
    return message.author.bot == False