import commandRegistry
import asyncio
import config
import logging
from models import TagReactables
from rolemessages import TMHCRoles, TestRoles

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

    session = metadata["session"]
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
        if(config.member_role[metadata.get("server").id] not in user.roles and role[0] not in user.roles):
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
            try:
                await channel.delete_messages(message_list)
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(e)
                for message in message_list:
                    await message.delete()
                    await asyncio.sleep(1)
            message_list = []
    try:
        await channel.delete_messages(message_list)
        await asyncio.sleep(1)
    except Exception as e:
        logger.error(e)
        for message in message_list:
            await message.delete()
            await asyncio.sleep(1)
    message_list = []

