import re

# Check if a string is a command
def is_command(string):
    if(string == None or len(string) == 0):
        return False

    return (string[0] == "." or string[0] == "/") and (".." not in string) and (len(string) > 1)


# Get a command and its arguments from a string. the command (case insensitive, alphanumeric) is element [0] and
# element [1] is the list of arguments (case sensitive, any characters)
def get_command(string):
    valid_characters = "abcdefghijklmnopqrstuvwxyz1234567890"
    command = string.split(" ")
    return [''.join([char for char in command[0][1:].lower() if char in valid_characters]), [arg.strip() for arg in command[1:] if arg.strip() != ""]]

def get_arg_string(command):
    return " ".join(command)

def is_parameterised(string):
    return (len(string) > 2 and string[0] == "(" and string[-1] == ")")

def asCommandArg(*args):
    return [[],[i for i in args]]
