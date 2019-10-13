import commandRegistry
import asyncio
import config
import logging
from models import Session, TagReactables
from rolemessages import TMHCRoles, TestRoles
from discord import ChannelType
import os

logger = logging.getLogger(__name__)

# Only log debug messages in debug mode
if (config.DEBUG):
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

commands = {}
command = commandRegistry.command
reaction = commandRegistry.reaction
restrictions = commandRegistry.restrictions
help_text = commandRegistry.help_text
tag_reactables = commandRegistry.tag_reactables

@help_text("Ping")
@command("ping")
async def ping(command, metadata, sendReply):
    return await sendReply("Pong")


@restrictions(config.servers.get("TMHCRND"))
@help_text("Vet a member for the server. \n\
           approve: vote to approve the member (requires at least two approvals).\n\
           deny: vote to deny the member (only one deny required, but if a deny occurs \
           after an approve one vetter must change their vote in order to approve or deny)\n\
           respond <message>: send a PM to the member in question.")
@command("vet")
async def vet(command, metadata, sendReply):
    if(command[1][0] == "approve"):
        pass
    elif(command[1][0] == "deny"):
        pass
    elif(command[1][0] == "respond"):
        pass

@restrictions(config.servers.get("TMHC"), config.servers.get("Test"))
@command("regenroles")
@help_text("Regenerate the roles text")
async def regenroles(command, metadata, sendReply):
    if(metadata["server"].id == config.servers["TMHC"]):
        rolearray = TMHCRoles.rolearray
    elif(metadata["server"].id == config.servers["Test"]):
        rolearray = TestRoles.rolearray
    else:
        return await sendReply("An error occurred!")
    
    guild = metadata["message"].guild
    channel = guild.get_channel(int(config.roles_channel.get(metadata["server"].id)))

    await clearChannel(channel)    
    
    for element in rolearray:
        if(isinstance(element, str)):
            await sendReply(element)
            await asyncio.sleep(1)
        elif(isinstance(element, tuple)):
            message = await sendReply(element[1])
            role = guild.get_role(int(element[0])) 

            if(role is None):
                return await sendReply("An error occurred!")

            await do_add_role_reactable(message, role.id, metadata)
            await asyncio.sleep(1)

@restrictions(config.servers.get("TMHC"), config.servers.get("Test"))
@command("addrolereactable")
@help_text("Allow reactions on a message to assign a role. Usage: 'addrolereactable <messageid> <roleid>' in the channel containing the message.")
async def addrolereactable(command, metadata, sendReply):
    if(len(command[1]) < 2):
        return await sendReply("Please specify a messageid and roleid")
    
    messageid = command[1][0]
    roleid = command[1][1]
    guild = metadata.get("client").get_guild(metadata.get("server").id)
    role = guild.get_role(int(roleid)) 
    
    if(role is None):
        return await sendReply("No role with that id was found")

    try:
        message = await metadata["message"].channel.fetch_message(messageid)
    except Exception as e:
        logger.exception(e)
        return await sendReply("No message with that id was found")
   
    await do_add_role_reactable(message, roleid, metadata)
    
    await metadata["message"].delete() # delete the invoking message
    return await sendReply("Added role react for "+role.name, delete_after=5)


async def do_add_role_reactable(message, roleid, metadata):
    emoji = "🔼"
    await message.add_reaction(emoji)

    session = Session()
    instance = session.query(TagReactables).filter_by(message_id=message.id).first()
    if(instance):
        instance.function_name="toggle_role"
        instance.function_args=roleid
    else:
        instance = TagReactables(message_id=message.id, function_name="toggle_role", function_args=roleid)
    session.add(instance)

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("Unable to commit to database: " + e)

@restrictions(config.servers.get("TMHC"), config.servers.get("Test"))
@tag_reactables()
async def accept_coc(args, event_type, metadata):
    if(event_type != "REACTION_ADD"):
        return
    
    roles = []
    guild = metadata.get("client").get_guild(metadata.get("server").id)

    for role in config.coc_roles[metadata.get("server").id]:
        roles.append(guild.get_role(role))

    try:
        user = guild.get_member(metadata.get("user").id)
        
        # ensure user is not already a member and does not already have the coc role
        if(guild.get_role(config.member_role[metadata.get("server").id]) not in user.roles and roles[0] not in user.roles):
            await guild.get_member(user.id).add_roles(*roles)
    except Exception as e:
        logger.exception(e)


@restrictions(config.servers.get("TMHC"), config.servers.get("Test"))
@tag_reactables()
async def toggle_role(args, event_type, metadata):
    guild = metadata.get("client").get_guild(metadata.get("server").id)
    role = guild.get_role(int(args))
    
    if(event_type == "REACTION_ADD"):    
        try:
            userid = metadata.get("user").id
            await guild.get_member(userid).add_roles(role)
        except Exception as e:
            logger.exception(e)
    elif(event_type == "REACTION_REMOVE"):
        try:
            userid = metadata.get("user").id
            await guild.get_member(userid).remove_roles(role)
        except Exception as e:
            logger.exception(e)



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
        if(str(message.author.id) == str(userid)):
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

@restrictions(config.servers.get("TMHC"), config.servers.get("Test"))
@command("gdpr")
@help_text("Compile GDPR data on a user. Usage: 'gdpr <userid>'.")
async def getGDPR(command, metadata, sendReply):

    filename = "gdprdata/data.txt"
    mymessage = await sendReply("Compiling GDPR data...")

    userid = command[1][0]
    guild = metadata["message"].guild
    
    with open(filename, 'w') as f:
        for channel in guild.channels:
            try:
                if channel.type == ChannelType.text:
                    await sendReply("Processing data for: " + str(channel), edit=mymessage)
                    async for message in channel.history(limit=None):
                        if isGDPRableMessage(message, userid):
                            f.write(messageToString(message))
            except Exception as e:
                await sendReply("Exception while processing channel: " + str(channel))
                logger.error(e)
                pass
    
    await sendReply("GDPR Data Compiled!", edit=mymessage)
    filesize = os.path.getsize(filename)

    if(filesize < 8*1000*1000):
        await sendReply("Data: ", file=filename)
    else:
        await sendReply("Data is too large ("+str(filesize)+" megabytes) to send via discord! :(")


@restrictions(config.servers.get("TMHC"), config.servers.get("Test"))
@command("gdprdelete")
@help_text("Delete all messages sent by a user. Usage: 'gdprdelete <userid>'.")
async def deleteGDPR(command, metadata, sendReply):
    userid = command[1][0]
    guild = metadata["message"].guild

    mymessage = await sendReply("Deleting messages sent by "+userid+" in compliance with gdpr.")

    for channel in guild.channels:
        try:
            if channel.type == ChannelType.text:
                await sendReply("Processing data for: " + str(channel), edit=mymessage)
                await clearChannelOfUser(channel, userid)
        except Exception as e:
            await sendReply("Exception while processing channel: " + str(channel))
            logger.error(e)
            pass
    
    await sendReply("Data for user " + str(userid) + " deleted!", edit=mymessage)



def isGDPRableMessage(message, userid):
    for user in message.mentions:
        if(str(user.id) == str(userid)):
            return True
    return str(message.author.id) == str(userid)


def messageToString(message):
    basestring = "Author: " + str(message.author.id) + "\n" + \
            "Server: " + str(message.guild.name) + "\n" + \
            "Channel: "+ str(message.channel.name) + "\n" + \
            "Message: " + str(message.content)

    attachments = "" if len(message.attachments) == 0 else "\nAttachments: " + str(message.attachments)
    terminator = "\n---------------------------------------\n"

    return basestring + attachments + terminator
