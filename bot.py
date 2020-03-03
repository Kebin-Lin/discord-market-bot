import os, math
import discord
from util import database
from util.extrafuncs import *

async def helpFunc(message, splitcontent):
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
    await message.channel.send(output)

async def listFunc(message, splitcontent):
    marketID = database.getMarket(message.channel.id)
    if marketID == None:
        await message.channel.send("Market not yet set")
    data = {
        'price:' : [],
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
    
    #Compliance checks
    if len(data['tags:']) > 10:
        await message.channel.send("Too many tags")
    for i in data['tags:']:
        if len(i) > 32:
            await message.channel.send("One or more tags are too long")

    if len(data['price:']) == 0:
        await message.channel.send("No price given")
    suffix = ''
    data['price:'] = data['price:'][0]
    if data['price:'][-1].isalpha():
        for i in range(len(data['price:']) - 1, 0, -1):
            if data['price:'][i].isnumeric():
                suffix = data['price:'][i + 1:]
                data['price:'] = data['price:'][:i + 1]
                break
    suffix = suffix.lower()
    if suffix not in ABBREVIATION_DICT:
        await message.channel.send("Invalid suffix")
    try:
        data['price:'] = eval(data['price:'])
    except:
        await message.channel.send("Invalid price")
    if data['price:'] < 0:
        await message.channel.send("Cannot list a negative price")
    data['price:'] *= ABBREVIATION_DICT[suffix]
    data['price:'] = roundSig(data['price:'])[0]

    data['notes:'] = ' '.join(data['notes:'])
    if len(data['notes:']) > 300:
        await message.channel.send("Notes too long")

    data['name:'] = ' '.join(data['name:'])
    if len(data['name:']) == 0:
        await message.channel.send("No name given")
    if len(data['name:']) > 64:
        await message.channel.send("Name too long")

    if database.addListing(marketID, message.author.id, data['name:'], roundSig(data['price:'])[0], data['notes:'], data['tags:']):
        await message.channel.send(f"Listing added: {str(data)}")
    else:
        await message.channel.send("Listing failed to be added, maybe you have too many listings?")

async def mylistingsFunc(message, splitcontent):
    marketID = database.getMarket(message.channel.id)
    if marketID == None:
        await message.channel.send("Market not yet set")
    listings = database.getListings(marketID, message.author.id)
    if len(listings) == 0:
        await message.channel.send("No listings found")
    embed = {
        # "title" : discord.Embed.Empty,
        # "description" : discord.Embed.Empty,
        # "url" : discord.Embed.Empty,
        "color" : 7855479,
        # "timestamp" : discord.Embed.Empty,
        # "footer" : discord.Embed.Empty,
        # "thumbnail" : discord.Embed.Empty,
        # "image" : discord.Embed.Empty,
        "author" : {
            "name" : f"{message.author.name}'s listings",
            "icon_url" : str(message.author.avatar_url)
        },
        "fields" : []
    }
    for i in listings:
        if i[4] % 1 != 0:
            shortenedPrice = shortenPrice(float(i[4]))
        else:
            shortenedPrice = shortenPrice(int(i[4]))
        notes = i[5]
        if len(notes) == 0:
            notes = "No notes"
        embed["fields"].append({
            "name": f"{i[3]} - {shortenedPrice}",
            "value": notes
        })
    await message.channel.send(embed = discord.Embed.from_dict(embed))

async def setmarketFunc(message, splitcontent):
    marketID = " ".join(splitcontent[2:])
    if len(marketID) == 0:
        await message.channel.send("No market name supplied")
    if len(marketID) > 64:
        await message.channel.send("Market name too long")
    database.setMarket(message.channel.id, marketID)
    await message.channel.send(f"Market set to {database.getMarket(message.channel.id)}")

COMMAND_SET = {
    'help' : {
        'helpmsg' : 'Prints out the list of commands available, !market help <cmd> for command usage',
        'usage' : '!market help <cmd>',
        'function' : helpFunc
    },
    'list' : {
        'helpmsg' : 'Lists a new item, prices are rounded to 4 significant figures',
        'usage' : '!market list name: <item name (max 64 characters)> price: <non negative number with up to two decimals> notes: <notes (max 300 characters)> tags: <tag1 (max 32 characters)> <tag2> ... <tag10>',
        'function' : listFunc
    },
    'mylistings' : {
        'helpmsg' : 'Lists out your listings in the market',
        'usage' : '!market mylistings',
        'function' : mylistingsFunc
    },
    'setmarket' : {
        'helpmsg' : 'Sets the market the bot will use in this channel',
        'usage' : '!market setmarket <market name (max 64 characters case sensitive)>',
        'function' : setmarketFunc
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
            await COMMAND_SET[splitcontent[1].lower()]['function'](message, splitcontent)
    # await message.channel.send(output)


client.run(os.environ["token"])