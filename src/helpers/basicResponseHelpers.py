import random
from helpers import fileHelpers

MAX_MESSAGE_SIZE = 2000

# Send a message in different parts
async def send_in_stages(message, sendReply):
    counter = 0

    # The maximum number of characters to send in one message
    breakMax = MAX_MESSAGE_SIZE

    while (counter+breakMax) < len(message):
        breakpoint = breakMax

        # Best to break at the end of a sentence
        for char in reversed(range(0, breakMax)):
            if message[counter+char] == ".":
                # Break at the first space after this full stop
                print(message[counter+char:])
                breakpoint = char+message[counter+char:].index(" ") + 1
                print(breakpoint)
                break

        print("passed ." + str(breakpoint))

        # If we cant break at the end of a sentence, break on the rightmost space we can find
        if breakpoint == breakMax:
            for char in reversed(range(0, breakMax)):
                if message[counter+char] == " ":
                    breakpoint = char + 1
                    break

            # Else breakpoint == breakMax and we will just have to break at whatever is there

        await sendReply(message[counter:counter+breakpoint])
        counter += breakpoint

    await sendReply(message[counter:])


# Get a random entry from a file, splitting on the delimiter given
async def randomResponseCommand(command, metadata, filePath, delimiter=None):
    lines = fileHelpers.parse_file_as_array(filePath, delimiter)
    index = random.randint(0,len(lines)-1)
    chosenLine = lines[index]

    return chosenLine

# Get a specified entry from a file
async def chosenResponseCommand(command, metadata, filePath, delimiter=None):

    if(len(command[1]) > 0):
        if (command[1][0].isdigit() and int(command[1][0]) > 0):
            selection = int(command[1][0])
            lines = fileHelpers.parse_file_as_array(filePath, delimiter)

            if(selection <= len(lines)):
                return lines[selection-1]
            else:
                return "Only " + str(len(lines)) + " choices available!"


    return await randomResponseCommand(command, metadata, filePath, delimiter)

#Interleave an array with a string symbol ( int + arr[0] + int + arr[1] + int...)
def interleave(array, interleaveString):
    if(len(array) > 0):
        return interleaveString + interleaveString.join(array) + interleaveString
    else:
        return interleaveString
