import os, sys

bot_name = "Eve Bot"

servers = {
    "Test": 384144475229782037,
    "TMHC": 354565059675947009,
    "TMHCRND": 371995067386429442
}

roles = {
    "TMHC": {
        "Mods": 501445228553699328,
        "Staff": 399654133470199820,
        "Owners": 354565435514945536,
        "Member": 559099713400602624,
        "404": 501818944567640084
    },
    "Test": {
        "Admin": 574564780350636032,
        "COC": 616655951193178114
    }
}
# Log channels for servers in the form (guild_id : channel id), one per guild.
# Message edits and deletes for each guild will be posted here.
log_channels = {
    servers["Test"]: 574416190802231316, # Test server
    servers["TMHC"]: 604787076021485589  # TMHC
}

# A list of role ids who are approved to use commands, keyed by guild id
approved_roles = {
    servers["Test"]: [roles["Test"]["Admin"]], # Test server
    servers["TMHC"]: [roles["TMHC"]["Mods"], roles["TMHC"]["Staff"], roles["TMHC"]["Owners"]] # TMHC
}

# Whether or not to run in debug mode is determined by the presence of an environment variable
DEBUG = os.environ.get('BOT_DEBUG', False) is not False

# If running in debug mode, the bot will be restricted to channel ids in the following array.
debug_channel_ids = [
    384144475670446081, # Test channels
    574416190802231316,
    616723907915022339
]

# The roles to assign after accepting the coc
coc_roles = {
    servers["TMHC"]: [roles["TMHC"]["404"]],
    servers["Test"]: [roles["Test"]["COC"]]
}

member_role = {
    servers["TMHC"]: roles["TMHC"]["Member"]
}

roles_channel = {
    servers["TMHC"]: 616700269589430274,
    servers["Test"]: 616723907915022339
}

warning_channel = {
    servers["TMHC"]: 501440580568743961,
    servers["Test"]: 805068865322221619
}

ROOT_DIR = os.path.dirname(sys.modules['__main__'].__file__)
RESPONSE_DIR = os.path.join(ROOT_DIR, "responses")
COMMAND_DIR = os.path.join(ROOT_DIR, "commands")
