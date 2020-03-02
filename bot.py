import os
import discord
import database

def helpFunc(message, splitcontent):
    output = ""
    if len(splitcontent) > 2:
        cmd = splitcontent[2].lower()
        if cmd in COMMAND_SET:
            output = f"{COMMAND_SET[cmd]['helpmsg']}\n{COMMAND_SET[cmd]['usage']}"
        else:
            output = 'Invalid command, for a list of commands, use !market help'
    else:
        for i in sorted(COMMAND_SET.keys()):
            output += f"{i} : {COMMAND_SET[i]['helpmsg']}\n"
    return output

def listFunc(message, splitcontent):
    data = {
        'name:' : [],
        'notes:' : [],
        'tags:' : []
    }
    curr = ""
    for i in range(2, len(splitcontent)):
        if splitcontent[i] in data:
            curr = splitcontent[i]
        elif curr != "":
            data[curr].append(splitcontent[i])
    if len(data['tags:']) > 10:
        return "Too many tags"
    for i in data['tags:']:
        if len(i) > 32:
            return "One or more tags are too long"
    data['notes:'] = ' '.join(data['notes:'])
    if len(data['notes:']) > 300:
        return "Notes too long"
    outputName = ' '.join(data['name:'])
    if len(outputName) > 64:
        return "Name too long"
    return str(data)


COMMAND_SET = {
    'help' : {
        'helpmsg' : 'Prints out the list of commands available, !market help <cmd> for command usage',
        'usage' : '!market help <cmd>',
        'function' : helpFunc
    },
    'list' : {
        'helpmsg' : 'Lists a new item',
        'usage' : '!market list name: <item name (max 64 characters)> notes: <notes (max 300 characters)> tags: <tag1 (max 32 characters)> <tag2> ... <tag10>',
        'function' : listFunc
    }
}

print("Starting Market Bot")

client = discord.Client()

@client.event
async def on_ready():
    print(f'Logged on as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user: #Ignore messages by self
        return
    
    if message.content.startswith('!market'):
        splitcontent = message.content.split()
        if len(splitcontent) <= 1 or splitcontent[1].lower() not in COMMAND_SET:
            await message.channel.send('Invalid command, for a list of commands, use !market help')
            return
        else:
            await message.channel.send(COMMAND_SET[splitcontent[1].lower()]['function'](message, splitcontent))

    # await message.channel.send(output)


client.run(os.environ["token"])