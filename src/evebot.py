from helpers import commandHelpers
import commandRegistry
import re
import config
import logging
from models import TagReactables, Session

logger = logging.getLogger(__name__)

# Only log debug messages in debug mode
if config.DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


class EveBot:

    def __init__(self, this_user):
        self.user = this_user

    async def read(self, message, metadata, send_reply):
        all_commands = commandRegistry.commandsDict
        all_reactions = commandRegistry.reactionsDict

        if metadata.get("user").id != self.user.id:
            # If this message is a command, read it
            if commandHelpers.is_command(message):
                command_name = commandHelpers.get_command(message)
                
                try:
                    command_func = all_commands[command_name[0]]
                    server = metadata.get("server")

                    if self.has_permission_for_server(server, command_func):
                        return await command_func(command_name, metadata, send_reply)

                except KeyError as err:
                    logger.debug("Couldn't find command " + str(err))
            
            # Scan message looking for content to react to
            return await self.do_reacts(all_reactions, message, metadata, send_reply)

    # React to things people say (not commands)
    async def do_reacts(self, all_reactions, message, metadata, send_reply):
        for reaction in all_reactions:
            if reaction in message.lower():
                # calls the reaction function with the only argument being the message that triggered the reaction
                return await all_reactions[reaction]([reaction, [message]], metadata, send_reply)
            else:
                regmatch = re.findall(reaction, message, re.IGNORECASE)

                if regmatch:
                    return await all_reactions[reaction]([reaction, [message]], metadata, send_reply)

    # Deal with users tagging messages with emojis
    async def do_tag_reacts(self, event_type, metadata):
        all_tag_reacts = commandRegistry.tagReactablesDict

        session = Session()
        reactable = session.query(TagReactables).filter_by(message_id=metadata.get("message").id).first()

        if reactable is None:
            return

        command = all_tag_reacts[reactable.function_name]
        server = metadata.get("server")

        if self.has_permission_for_server(server, command):
            return await command(reactable.function_args, event_type, metadata)

    def has_permission_for_server(self, server, command):
        all_restrictions = commandRegistry.restrictionsDict

        return all_restrictions.get(command, None) is None \
                            or server.id in all_restrictions.get(command)
