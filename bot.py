import os, math
import discord
import database

ABBREVIATIONS = ['', 'k', 'mil', 'bil', 'tril']
ABBREVIATION_DICT = {
    '' : 1,
    'k' : 1000,
    'm' : 1000000,
    'mil' : 1000000,
    'b' : 1000000000,
    'bil' : 1000000000,
    't' : 1000000000000,
    'tril' : 1000000000000
}

def roundSig(n):
    power = int(math.floor(math.log10(abs(n))))
    if power < 1:
        power = 0
        return round(n, 2), power
    return round(n, 4 - int(math.floor(math.log10(abs(n)))) - 1), power

def shortenPrice(price):
    price, power = roundSig(price)
    if power // 3 == 0:
        return str(price)
    if power > 14:
        return "{:.3e}".format(price)
    return str(price / (10 ** (power // 3 * 3))) + ABBREVIATIONS[power // 3]

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
    return output, None

def listFunc(message, splitcontent):
    marketID = database.getMarket(message.channel.id)
    if marketID == None:
        return "Market not yet set", None
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
        return "Too many tags", None
    for i in data['tags:']:
        if len(i) > 32:
            return "One or more tags are too long", None

    if len(data['price:']) == 0:
        return "No price given", None
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
        return "Invalid suffix", None
    try:
        data['price:'] = eval(data['price:'])
    except:
        return "Invalid price", None
    if data['price:'] < 0:
        return "Cannot list a negative price", None
    data['price:'] *= ABBREVIATION_DICT[suffix]
    data['price:'] = roundSig(data['price:'])[0]

    data['notes:'] = ' '.join(data['notes:'])
    if len(data['notes:']) > 300:
        return "Notes too long", None

    data['name:'] = ' '.join(data['name:'])
    if len(data['name:']) == 0:
        return "No name given", None
    if len(data['name:']) > 64:
        return "Name too long", None

    # return str(data['price:']), None
    if database.addListing(marketID, message.author.id, data['name:'], roundSig(data['price:'])[0], data['notes:'], data['tags:']):
        return f"Listing added: {str(data)}", None
    else:
        return "Listing failed to be added, maybe you have too many listings?", None

def mylistingsFunc(message, splitcontent):
    marketID = database.getMarket(message.channel.id)
    if marketID == None:
        return "Market not yet set", None
    listings = database.getListings(marketID, message.author.id)
    if len(listings) == 0:
        return "No listings found", None
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
        embed["fields"].append({
            "name": f"{i[3]} - {shortenedPrice}",
            "value": i[5] #Notes
        })
    return None, discord.Embed.from_dict(embed)

def setmarketFunc(message, splitcontent):
    marketID = " ".join(splitcontent[2:])
    if len(marketID) == 0:
        return "No market name supplied", None
    if len(marketID) > 64:
        return "Market name too long", None
    database.setMarket(message.channel.id, marketID)
    return f"Market set to {database.getMarket(message.channel.id)}", None

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
            outputcontent, outputembed = COMMAND_SET[splitcontent[1].lower()]['function'](message, splitcontent)
            await message.channel.send(content = outputcontent, embed = outputembed)

    # await message.channel.send(output)


client.run(os.environ["token"])