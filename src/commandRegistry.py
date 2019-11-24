from helpers import basicResponseHelpers
import config

commandsDict={}
reactionsDict={}
restrictionsDict={}
help_texts = {}
tagReactablesDict = {}

__all__ = {}
__all__["commands"] = commandsDict
__all__["reactions"] = reactionsDict
__all__["restrictions"] = restrictionsDict
__all__["tagreactables"] = tagReactablesDict

def restrictions(*servers):
    def registrar(function):
        restrictionsDict[function] = servers

    return registrar

def command(*commandNames):
    def registrar(function):
        for commandName in commandNames:
            commandsDict[commandName] = function
        return function

    return registrar

def reaction(*reactionNames):
    def registrar(function):
        for reactionName in reactionNames:
            reactionsDict[reactionName] = function
        return function

    return registrar

def help_text(text):
    def registrar(function):
        help_texts[function.__name__] = text
        return function

    return registrar

def tag_reactables():
    def registrar(function):
        tagReactablesDict[function.__name__] = function
        return function
    return registrar

def get_help_message(server):
    helpData = {}

    # get help data (commands, their aliases, and their help text)
    for given_command in commandsDict:
        command_func = commandsDict[given_command]
        function_name = commandsDict[given_command].__name__
        
        # If help text exists for this command and the command is able to be used in the server
        if function_name in help_texts.keys() and (restrictionsDict.get(command_func, None) is None or server in restrictionsDict.get(command_func, None)):
            if not (function_name in helpData.keys()):
                helpData[function_name] = {"helpText": help_texts[function_name], "aliases": [given_command]}
            else:
                helpData[function_name]["aliases"].append(given_command)

    help_message = "Help for "+config.bot_name+":\n"
    for the_command in sorted(helpData.keys()):
        help_message += "- "
        help_message += ", ".join(helpData[the_command]["aliases"])
        help_message += ": " + helpData[the_command]["helpText"] + "\n"

    return help_message


# Import all other commands and add them to the commands file
from commands import *

# Generate help text
@help_text("This command will display help text.")
@command("help")
async def help(command, metadata, sendReply):
    help_message = get_help_message(metadata["server"].id)
    await basicResponseHelpers.send_in_stages(help_message, sendReply)
