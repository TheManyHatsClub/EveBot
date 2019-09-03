from helpers import commandHelpers
import commandRegistry
import re
import config
import logging
from models import TagReactables, Session

logger = logging.getLogger(__name__)

# Only log debug messages in debug mode
if (config.DEBUG):
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

class EveBot:
    
    #React to things people say (not commands)
    async def doReacts(self, allReactions, message, metadata, sendReply):
        for reaction in allReactions:
            if(reaction in message.lower()):
                #calls the reaction function with the only argument being the message that triggered the reaction
                return await allReactions[reaction]([reaction, [message]], metadata, sendReply)
            else:
                regmatch = re.findall(reaction, message, re.IGNORECASE)

                if(regmatch):
                    return await allReactions[reaction]([reaction, [message]], metadata, sendReply)

    async def read(self, message, metadata, sendReply):
        allCommands = commandRegistry.commandsDict
        allReactions = commandRegistry.reactionsDict
        allRestrictions = commandRegistry.restrictionsDict
        
        if(metadata.get("user").id != self.user.id):
            # If this message is a command, read it
            if(commandHelpers.is_command(message)):
                command = commandHelpers.get_command(message)
                
                try:

                    command_func = allCommands[command[0]]

                    if(allRestrictions.get(command_func, None) is None):
                        return await command_func(command, metadata, sendReply)
                    elif(metadata.get("server").id in allRestrictions.get(command_func)):
                        return await command_func(command, metadata, sendReply)

                except KeyError as err:
                    logger.debug("Couldn't find command " + str(err))
            
            # Scan message looking for content to react to
            return await self.doReacts(allReactions, message, metadata, sendReply)

    # Deal with users tagging messages with emojis
    async def doTagReacts(self, event_type, metadata):
        allTagReacts = commandRegistry.tagReactablesDict
        allRestrictions = commandRegistry.restrictionsDict
        
        session = Session()
        reactable = session.query(TagReactables).filter_by(message_id=metadata.get("message").id).first()

        if(reactable is None):
            return

        command = allTagReacts[reactable.function_name]
        
        if(allRestrictions.get(command, None) is None):
            return await command(reactable.function_args, event_type, metadata)
        elif(metadata.get("server").id in allRestrictions.get(command)):
            return await command(reactable.function_args, event_type, metadata)

    def __init__(self, thisUser):
        self.user = thisUser
