import os, math, asyncio
import discord
from util import database
from util.extrafuncs import *

client = discord.Client()

async def helpFunc(message, splitcontent):
    embed = {
        "color" : 7855479,
        "author" : {
            "name" : "Command List",
            "icon_url" : str(client.user.avatar_url)
        },
        "fields" : []
    }
    if len(splitcontent) > 2:
        cmd = splitcontent[2].lower()
        if cmd in COMMAND_SET:
            if 'alias' in COMMAND_SET[cmd]:
                cmd = COMMAND_SET[cmd]['alias']
            embed['author']['name'] = f"!market {cmd}"
            embed['fields'].append({
                'name' : "Description",
                'value' : COMMAND_SET[cmd]['helpmsg']
            })
            embed['fields'].append({
                'name' : "Usage",
                'value' : COMMAND_SET[cmd]['usage']
            })
        else:
            await message.channel.send('Invalid command, for a list of commands, use !market help')
            return
    else:
        for i in sorted(COMMAND_SET.keys()):
            if 'alias' not in COMMAND_SET[i]:
                embed['fields'].append({
                    "name" : i,
                    "value" : COMMAND_SET[i]['helpmsg']
                })
    await message.channel.send(embed = discord.Embed.from_dict(embed))

async def listFunc(message, splitcontent):
    marketID = database.getMarket(message.channel.id)
    if marketID == None:
        await message.channel.send("Market not yet set")
        return
    if database.isPublic(marketID):
        if not database.isMember(marketID, message.author.id):
            database.updateMember(marketID, message.author.id)
    elif not database.isMember(marketID, message.author.id):
        await message.channel.send("User is not a member of this market")
        return
    data = {
        'price:' : [],
        'name:' : [],
        'notes:' : []
    }
    curr = ""
    for i in range(2, len(splitcontent)):
        if splitcontent[i] in data:
            curr = splitcontent[i]
        elif curr != "":
            data[curr].append(splitcontent[i])
    
    #Compliance checks
    if len(data['price:']) == 0:
        await message.channel.send("No price given")
        return
    suffix = ''
    data['price:'] = data['price:'][0]
    if data['price:'][-1].isalpha():
        for i in range(len(data['price:']) - 1, -1, -1):
            if data['price:'][i].isnumeric():
                suffix = data['price:'][i + 1:]
                data['price:'] = data['price:'][:i + 1]
                break
    suffix = suffix.lower()
    if suffix not in ABBREVIATION_DICT:
        await message.channel.send("Invalid suffix")
        return
    try:
        data['price:'] = eval(data['price:'])
    except:
        await message.channel.send("Invalid price")
        return
    if data['price:'] < 0:
        await message.channel.send("Cannot list a negative price")
        return
    data['price:'] *= ABBREVIATION_DICT[suffix]
    data['price:'] = roundSig(data['price:'])[0]
    if data['price:'] > 9.999e99:
        await message.channel.send("Price too large")
        return

    data['notes:'] = ' '.join(data['notes:'])
    if len(data['notes:']) > 300:
        await message.channel.send("Notes too long")
        return

    data['name:'] = ' '.join(data['name:'])
    if len(data['name:']) == 0:
        await message.channel.send("No name given")
        return
    if len(data['name:']) > 64:
        await message.channel.send("Name too long")
        return

    if database.addListing(marketID, message.author.id, data['name:'], data['price:'], data['notes:']):
        embed = {
            "color" : 7855479,
            "author" : {
                "name" : "Listing Created",
                "icon_url" : str(client.user.avatar_url)
            },
            "fields" : [{'name' : f"{data['name:']} - {shortenPrice(data['price:'])}", 'value' : data['notes:'] if len(data['notes:']) != 0 else "No notes"}]
        }
        await message.channel.send(embed = discord.Embed.from_dict(embed))
    else:
        await message.channel.send("Listing failed to be added, maybe you have too many listings?")

async def mylistingsFunc(message, splitcontent):
    marketID = database.getMarket(message.channel.id)
    if marketID == None:
        await message.channel.send("Market not yet set")
        return
    listings = database.getListings(marketID, message.author.id)
    if len(listings) == 0:
        await message.channel.send("No listings found")
        return
    embed = {
        # "title" : discord.Embed.Empty,
        # "description" : discord.Embed.Empty,
        # "url" : discord.Embed.Empty,
        "color" : 7855479,
        # "timestamp" : discord.Embed.Empty,
        "footer" : {
            "text": "Press ❌ to toggle deletion mode, then click on a number to delete the listing"
        },
        # "thumbnail" : discord.Embed.Empty,
        # "image" : discord.Embed.Empty,
        "author" : {
            "name" : f"{message.author.name}'s listings",
            "icon_url" : str(message.author.avatar_url)
        },
        "fields" : []
    }

    offset = 0
    reactions = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟','◀️','▶️','❌']

    def setupListings(embed, listings):
        embed["fields"] = []
        emotectr = 0
        for i in listings[offset : offset + 10]:
            if i[4] >= 1000 or i[4] % 1 != 0:
                shortenedPrice = shortenPrice(float(i[4]))
            else:
                shortenedPrice = shortenPrice(int(i[4]))
            notes = i[5]
            if len(notes) == 0:
                notes = "No notes"
            embed["fields"].append({
                "name": f"{reactions[emotectr]} {i[3]} - {shortenedPrice}",
                "value": notes
            })
            emotectr += 1
    setupListings(embed, listings)
    sentMsg = await message.channel.send(embed = discord.Embed.from_dict(embed))
    
    for i in range(min(10, len(listings))):
        await sentMsg.add_reaction(reactions[i])
    for i in range(10, 13):
        await sentMsg.add_reaction(reactions[i])

    def check(reaction, user):
        return reaction.message.id == sentMsg.id and user == message.author and str(reaction.emoji) in reactions

    waitForReaction = True
    removemode = False

    while waitForReaction:
        try:
            done, pending = await asyncio.wait(
                [
                    client.wait_for('reaction_add', check = check),
                    client.wait_for('reaction_remove', check = check)
                ],
                return_when = asyncio.FIRST_COMPLETED,
                timeout = 30,
            )
            #Cancel other task
            gather = asyncio.gather(*pending)
            gather.cancel()
            try:
                await gather
            except asyncio.CancelledError:
                pass
            if len(done) == 0:
                raise asyncio.TimeoutError('No change in reactions')
            reaction = done.pop().result()[0]
        except asyncio.TimeoutError:
            waitForReaction = False
            embed['color'] = 0xff6961
            await sentMsg.edit(embed = discord.Embed.from_dict(embed))
        else:
            emote = str(reaction.emoji)
            match = -1
            for i in range(12, -1, -1): #Search for matching emote in emote list
                if reactions[i] == emote:
                    match = i
                    break
            if match == 12: #X selected
                removemode = not removemode
            elif match == 11: #Next page
                if offset + 10 < len(listings):
                    offset += 10
                    setupListings(embed, listings)
                    await sentMsg.edit(embed = discord.Embed.from_dict(embed))
            elif match == 10: #Previous page
                if offset - 10 >= 0:
                    offset -= 10
                    setupListings(embed, listings)
                    await sentMsg.edit(embed = discord.Embed.from_dict(embed))
            else:
                if removemode and offset + match < len(listings):
                    database.removeListing(listings[offset + match][0])
                    del listings[offset + match]
                    if len(listings) != 0 and not(offset < len(listings)):
                        offset -= 10
                    setupListings(embed, listings)
                    await sentMsg.edit(embed = discord.Embed.from_dict(embed))

async def setmarketFunc(message, splitcontent):
    if message.guild != None:
        if not message.author.guild_permissions.administrator:
            await message.channel.send("Non admins cannot set the market name in a server")
            return
    marketID = " ".join(splitcontent[2:])
    if len(marketID) == 0:
        await message.channel.send("No market name supplied")
        return
    if len(marketID) > 64:
        await message.channel.send("Market name too long")
        return
    if database.setMarket(message.channel.id, marketID):
        await message.channel.send(f'Market set to "{database.getMarket(message.channel.id)}"')
    else:
        await message.channel.send("Market does not exist")

async def createmarketFunc(message, splitcontent):
    if message.guild != None:
        await message.channel.send("Markets cannot be created from a server")
        return
    marketID = " ".join(splitcontent[2:])
    if len(marketID) == 0:
        await message.channel.send("No market name supplied")
        return
    if len(marketID) > 64:
        await message.channel.send("Market name too long")
        return
    if database.createMarket(marketID, message.author.id):
        await message.channel.send(f'Market "{marketID}" created')
        database.updateMember(marketID, message.author.id, isadmin = True)
    else:
        await message.channel.send("Market already exists")

async def searchFunc(message, splitcontent):
    marketID = database.getMarket(message.channel.id)
    if marketID == None:
        await message.channel.send("Market not yet set")
        return
    if len(splitcontent) < 3:
        await message.channel.send("No query supplied")
        return
    query = ' '.join(splitcontent[2:])
    listings = database.search(marketID, query)
    if len(listings) == 0:
        await message.channel.send("No listings found")
        return
    embed = {
        "color" : 7855479,
        "footer" : {
            "text": "Press ❗ to toggle notification mode, then click on a number to notify the seller"
        },
        "author" : {
            "name" : "Search Results",
            "icon_url" : str(client.user.avatar_url)
        },
        "fields" : []
    }

    offset = 0
    reactions = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟','◀️','▶️','❗']
    notifiedset = set()

    def setupListings(embed, listings):
        embed["fields"] = []
        emotectr = 0
        for i in listings[offset : offset + 10]:
            if i[4] >= 1000 or i[4] % 1 != 0:
                shortenedPrice = shortenPrice(float(i[4]))
            else:
                shortenedPrice = shortenPrice(int(i[4]))
            notes = i[5]
            if len(notes) == 0:
                notes = "No notes"
            embed["fields"].append({
                "name": f"{'❗' if offset + emotectr in notifiedset else reactions[emotectr]} {i[3]} - {str(client.get_user(i[2]))} - {shortenedPrice}",
                "value": notes
            })
            emotectr += 1
    setupListings(embed, listings)
    sentMsg = await message.channel.send(embed = discord.Embed.from_dict(embed))
    for i in range(min(10, len(listings))):
        await sentMsg.add_reaction(reactions[i])
    for i in range(10, 13):
        await sentMsg.add_reaction(reactions[i])

    def check(reaction, user):
        return reaction.message.id == sentMsg.id and user == message.author and str(reaction.emoji) in reactions

    waitForReaction = True
    notifymode = False

    while waitForReaction:
        try:
            done, pending = await asyncio.wait(
                [
                    client.wait_for('reaction_add', check = check),
                    client.wait_for('reaction_remove', check = check)
                ],
                return_when = asyncio.FIRST_COMPLETED,
                timeout = 30,
            )
            #Cancel other task
            gather = asyncio.gather(*pending)
            gather.cancel()
            try:
                await gather
            except asyncio.CancelledError:
                pass
            if len(done) == 0:
                raise asyncio.TimeoutError('No change in reactions')
            reaction = done.pop().result()[0]
        except asyncio.TimeoutError:
            waitForReaction = False
            embed['color'] = 0xff6961
            await sentMsg.edit(embed = discord.Embed.from_dict(embed))
        else:
            emote = str(reaction.emoji)
            match = -1
            for i in range(12, -1, -1): #Search for matching emote in emote list
                if reactions[i] == emote:
                    match = i
                    break
            if match == 12: #X selected
                notifymode = not notifymode
            elif match == 11: #Next page
                if offset + 10 < len(listings):
                    offset += 10
                    setupListings(embed, listings)
                    await sentMsg.edit(embed = discord.Embed.from_dict(embed))
            elif match == 10: #Previous page
                if offset - 10 >= 0:
                    offset -= 10
                    setupListings(embed, listings)
                    await sentMsg.edit(embed = discord.Embed.from_dict(embed))
            else:
                if notifymode and offset + match < len(listings) and offset + match not in notifiedset:
                    notifiedset.add(offset + match)
                    setupListings(embed, listings)
                    await sentMsg.edit(embed = discord.Embed.from_dict(embed))
                    lister = client.get_user(listings[offset + match][2])
                    if lister.dm_channel == None:
                        await lister.create_dm()
                    await lister.dm_channel.send(f'<@{message.author.id}> is interested in your item named "{listings[offset + match][3]}"')

async def addmemberFunc(message, splitcontent):
    marketID = database.getMarket(message.channel.id)
    if marketID == None:
        await message.channel.send("Market not yet set")
        return
    if not database.isAdmin(marketID, message.author.id):
        await message.channel.send("User is not an admin of this market")
        return
    if len(splitcontent) < 3:
        await message.channel.send("No user supplied")
        return
    memberID = None
    if len(message.mentions) != 0:
        memberID = message.mentions[0].id
    else:
        try:
            memberID = client.get_user(eval(splitcontent[3])).id
        except:
            await message.channel.send("Invalid user id")
            return
    database.updateMember(marketID, memberID)
    await message.channel.send("Member added")

async def setadminFunc(message, splitcontent):
    marketID = database.getMarket(message.channel.id)
    if marketID == None:
        await message.channel.send("Market not yet set")
        return
    if not database.isOwner(marketID, message.author.id):
        await message.channel.send("User is not the owner of this market")
        return
    if len(splitcontent) < 3:
        await message.channel.send("No user supplied")
        return
    memberID = None
    if len(message.mentions) != 0:
        memberID = message.mentions[0].id
    else:
        try:
            memberID = client.get_user(eval(splitcontent[3])).id
        except:
            await message.channel.send("Invalid user id")
            return
    database.updateMember(marketID, memberID, isadmin = True)
    await message.channel.send("Admin set")

async def demoteFunc(message, splitcontent):
    marketID = database.getMarket(message.channel.id)
    if marketID == None:
        await message.channel.send("Market not yet set")
        return
    if not database.isOwner(marketID, message.author.id):
        await message.channel.send("User is not the owner of this market")
        return
    if len(splitcontent) < 3:
        await message.channel.send("No user supplied")
        return
    memberID = None
    if len(message.mentions) != 0:
        memberID = message.mentions[0].id
    else:
        try:
            memberID = client.get_user(eval(splitcontent[3])).id
        except:
            await message.channel.send("Invalid user id")
            return
    database.updateMember(marketID, memberID, isadmin = False)
    await message.channel.send("User demoted")

async def kickFunc(message, splitcontent):
    marketID = database.getMarket(message.channel.id)
    if marketID == None:
        await message.channel.send("Market not yet set")
        return
    if not database.isAdmin(marketID, message.author.id):
        await message.channel.send("User is not an admin of this market")
        return
    if len(splitcontent) < 3:
        await message.channel.send("No user supplied")
        return
    memberID = None
    if len(message.mentions) != 0:
        memberID = message.mentions[0].id
    else:
        try:
            memberID = client.get_user(eval(splitcontent[3])).id
        except:
            await message.channel.send("Invalid user id")
            return
    if database.removeMember(marketID, memberID):
        await message.channel.send("User removed")
    else:
        await message.channel.send("User not a member")

async def setpublicityFunc(message, splitcontent):
    marketID = database.getMarket(message.channel.id)
    if marketID == None:
        await message.channel.send("Market not yet set")
        return
    if not database.isOwner(marketID, message.author.id):
        await message.channel.send("User is not the owner of this market")
        return
    if len(splitcontent) < 3:
        await message.channel.send("No publicity supplied")
        return
    publicitydict = {'public' : True, 'private' : False}
    publicity = splitcontent[2].lower()
    if publicity not in publicitydict:
        await message.channel.send("Invalid publicity")
        return
    database.changePublic(marketID, publicitydict[publicity])
    await message.channel.send(f"Market set to {publicity}")

COMMAND_SET = {
    'help' : {
        'helpmsg' : 'Prints out the list of commands available, !market help <cmd> for command usage',
        'usage' : '!market help <cmd>',
        'function' : helpFunc
    },
    'list' : {
        'helpmsg' : 'Lists a new item, prices are rounded to 4 significant figures and listings expire after 7 days',
        'usage' : '!market list name: <item name (max 64 characters)> price: <non negative number with up to two decimals> notes: <notes (max 300 characters)>',
        'function' : listFunc
    },
    'mylistings' : {
        'helpmsg' : 'Lists out your listings in the market, alias: ml',
        'usage' : '!market mylistings',
        'function' : mylistingsFunc
    },
    'ml' : {
        'alias' : 'mylistings'
    },
    'setmarket' : {
        'helpmsg' : 'Sets the market the bot will use in this channel',
        'usage' : '!market setmarket <market name (max 64 characters case sensitive)>',
        'function' : setmarketFunc
    },
    'search' : {
        'helpmsg' : 'Searches the market for items',
        'usage' : '!market search <query>',
        'function' : searchFunc
    },
    'createmarket' : {
        'helpmsg' : 'Creates a new market. Created markets are private by default. Can only be used in DMs',
        'usage' : '!market createmarket <market name (max 64 characters case sensitive)>',
        'function' : createmarketFunc
    },
    'addmember' : {
        'helpmsg' : 'Adds a member to the market, can only be used by admins',
        'usage' : '!market addmember <mention or user id>',
        'function' : addmemberFunc
    },
    'setadmin' : {
        'helpmsg' : 'Sets a member as an admin of the market, can only be used by the market owner',
        'usage' : '!market setadmin <mention or user id>',
        'function' : setadminFunc
    },
    'demote' : {
        'helpmsg' : 'Sets a member as a non-admin user, can oly be used by the market owner',
        'usage' : '!market demote <mention or user id>',
        'function' : demoteFunc
    },
    'kick' : {
        'helpmsg' : 'Removes a member from the market and deletes their listings, can only be used by admins',
        'usage' : '!market kick <mention or user id>',
        'function' : kickFunc
    },
    'setpublicity' : {
        'helpmsg' : 'Sets the publicity of a market, can only be used by the market owner',
        'usage' : '!market setpublicity <public|private>',
        'function' : setpublicityFunc
    }
}

print("Starting Market Bot")

@client.event
async def on_ready():
    print(f'Logged on as {client.user}')
    await client.change_presence(activity = discord.Game(name = 'Use "!market help" for a list of commands'))

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
            cmd = splitcontent[1].lower()
            if 'alias' in COMMAND_SET[cmd]:
                cmd = COMMAND_SET[cmd]['alias']
            await COMMAND_SET[cmd]['function'](message, splitcontent)
    # await message.channel.send(output)

client.run(os.environ["token"])