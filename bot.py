# bot.py
import os
import random
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv
import sqlite3
from PIL import Image

import newcard
from helperfuncs import *

print("imports successful")

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DB_PATH = GUILD + "_cards.db"

# This example requires the 'message_content' intent.

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix="<", intents=intents)


class Select(discord.ui.Select):
    def __init__(self, options, info, initiator):
        super().__init__(placeholder="Select an option",max_values=1,min_values=1,options=options)
        self.info = info
        self.initiator = initiator
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.initiator.id:
            filename = getcard(self.info[self.values[0]])
            file = discord.File(filename) # an image in the same folder as the main bot file
            embed = discord.Embed() # any kwargs you want here
            embed.set_image(url=f"attachment://{filename}")
            print(embed, file, filename, self.values[0])
            await interaction.response.send_message(content=f"Displaying {self.values[0]}'s card", file=file,ephemeral=True)

class SelectView(discord.ui.View):
    def __init__(self, *, select: Select, timeout = 180):
        super().__init__(timeout=timeout)
        self.add_item(select)

def getcard(member):
    results = executesql(DB_PATH, f"SELECT nation, quote, public FROM members WHERE members.memberid = {member.id}")[0]
    stats, pos = newcard.getstats(member.id)
    nat = results[0]
    quote = results[1]
    name = member.nick if member.nick else member.name
    img, _ = newcard.newcard(name, stats, pos, member.avatar, "cards/" + member.name + ".png", nat, quote)
    path = "tmp/card.png"
    img.save(path)
    return path
    

def createcard(dsc_id):
    executesql(DB_PATH, f"INSERT INTO members VALUES ({dsc_id}, '', '', FALSE)")
    executesql(DB_PATH, f"INSERT INTO memberhas (memberid, cardid, quantity) VALUES({dsc_id}, {dsc_id}, -1)")

def verifycard(dsc_id):
    results = executesql(DB_PATH, f"SELECT 1 FROM members WHERE memberid = {dsc_id}")
    return (True if results else False)

def verifyhascard(dsc_id, card_id):
    results = executesql(DB_PATH, f"SELECT quantity FROM memberhas WHERE memberid = {dsc_id} AND cardid = {card_id}")
    return (results if results else False)

@bot.command(name="quit", help="Stops the bot", category="Admins only")
async def quit(ctx):
    role = discord.utils.get(ctx.guild.roles, name="admin")
    if role not in ctx.author.roles:
        await ctx.send("Not an admin, you are not authorised to perform this command.")
        return 
    else:
        sys.exit()

@bot.command(name="init", help="Creates the database for that server if it doesn't exist", category="Admins only")
async def init(ctx):
    role = discord.utils.get(ctx.guild.roles, name="admin")
    if role not in ctx.author.roles:
        await ctx.send("Not an admin, you are not authorised to perform this command.")
        return 
    else:
        if not os.path.isfile(DB_PATH):
            sqlite3.connect(DB_PATH)
            executesql(DB_PATH, "CREATE TABLE IF NOT EXISTS members (memberid INTEGER PRIMARY KEY, nation STRING, quote STRING, public STRING)")
            print("1 created")
            executesql(DB_PATH, "CREATE TABLE IF NOT EXISTS memberhas (membercardid INTEGER PRIMARY KEY AUTOINCREMENT, memberid INTEGER, cardid INTEGER, quantity INTEGER)")
            print('2 created')
            executesql(DB_PATH, "CREATE TABLE IF NOT EXISTS trades (tradeid INTEGER PRIMARY KEY AUTOINCREMENT, initmemberid INTEGER, cardoffered INTEGER, cardreceived INTEGER, status BOOLEAN, acceptmemberid INTEGER)")
    await ctx.send("Initialisation successful for " + GUILD)

@bot.command(name="viewcards", help="Search and view public cards! Usage: <viewcards [search terms]")
async def viewcards(ctx, terms=None):
        if terms: terms = terms.lower()
        results = executesql(DB_PATH, f"SELECT memberid FROM members WHERE public=True")
        if not results:
                await ctx.send("No public cards found!")
                return
        else:
                options = []
                info = dict()
                for (cardid) in results:
                        cardid = cardid[0]
                        user = discord.utils.get(ctx.guild.members, id=cardid)
                        if (not terms) or (terms in str(user.name).lower()) or (terms in str(user.nick).lower()):
                                name = user.nick if user.nick else user.name
                                options.append(discord.SelectOption(label=name))
                                info[name] = user
                if not options: await ctx.send("No results found...check your input or try more generic keywords!")
                else:
                        selectmenu = Select(options, info, ctx.author)
                        await ctx.send("Here are the results we found:", view=SelectView(select=selectmenu))

@bot.command(name="setpublic", help="Sets your card as public. Admins can set others' cards to be public. Usage: <setpublic [user]")
async def setpublic(ctx, member: discord.Member = None):
    if member == None:
        msg = setattr(ctx, "public", "1")
    else:
        msg = setattr(ctx, "public", member, "1")
    await ctx.send(msg)

@bot.command(name="setprivate", help="Sets your card as private. Admins can set others' cards as private. Usage: <setprivate [user]")
async def setprivate(ctx, member: discord.Member = None):
    if member == None:
        msg = setattr(ctx, "public", "0")
    else:
        msg = setattr(ctx, "public", member, "0")
    await ctx.send(msg)

@bot.command(name="setnation", help="Sets your nationality. This will be shown on your card as a flag. Please use the two letter flag codes, eg. US for the United States, GB for Great Britain, etc. Check the Discord flag emoji codes if you're unsure. Usage: <setnation [nation] Admins can set other members' nationalities. Usage: <setnation [user] [nation]")
async def setnation(ctx, arg, optional=None):
    if arg.isalpha():
        arg = arg.lower()
    elif optional.isalpha():
        optional = optional.lower()
    msg = setattr(ctx, "nation", arg, optional)
    await ctx.send(msg)

@bot.command(name="setquote", help="Sets your quote. Please use double quotes around your quote if it contains spaces. Usage: <setquote [quote]. Admins can set others' quotes. Usage: <setquote [user] [quote] for admins.")
async def setquote(ctx, arg, optional=None):
    if (arg and len(arg) > 50) or (optional and len(optional) > 50):
        await ctx.send("50 characters are the maximum for a quote!")
        return
    msg = setattr(ctx, "quote", arg, optional)
    await ctx.send(msg)

def setattr(ctx, attr, arg, optional=None):
    adminrole = discord.utils.get(ctx.guild.roles, name="admin")
    if adminrole in ctx.author.roles:
        print(arg, type(arg))
        if optional:
            if type(arg) != discord.member.Member:
                try:
                    arg = ctx.message.guild.get_member(int(arg))
                except:
                    return "Please use double quotes around quotes."
            hascard, _ = newcard.getstats(arg.id)
            if not hascard:
                return f"{arg.name} doesn't have enough points yet!"
            if not verifycard(arg.id):
                createcard(arg.id)
            results = executesql(DB_PATH, f"UPDATE members SET {attr}='{optional}' WHERE members.memberid = {arg.id}")
            return f"Set {arg.name}'s {attr} to {optional}!"
        else:
            hascard, _ = newcard.getstats(ctx.author.id)
            if not hascard:
                return f"{ctx.author.name} doesn't have enough points yet!"
            if not verifycard(ctx.author.id):
                createcard(ctx.author.id)
            results = executesql(DB_PATH, f"UPDATE members SET {attr}='{arg}' WHERE members.memberid = {ctx.author.id}")
            return f"Set {ctx.author.name}'s {attr} to {arg}!"

    if (not arg.isalpha()) and (not len(arg) == 2) and (attr == "nation"):
        return "Use the two letter flag codes, eg. US for USA, GB for Great Britain etc."
    hascard, _ = newcard.getstats(ctx.author.id)
    if not hascard:
        return "You don't have enough points yet! Get 5,000 points for UNION to get your own card!"
    else:
        if not verifycard(ctx.author.id):
            createcard(ctx.author.id)
        results = executesql(DB_PATH, f"UPDATE members SET {attr}='{arg}' WHERE members.memberid = {ctx.author.id}")
        return f"Set {ctx.author.nick if ctx.author.nick else ctx.author.name}'s {attr} to {arg}!"


@bot.command(name="gift", help="Gifts your card to another member free of charge. Usage: <gift [user] . Admins can gift other member's cards to others. Usage: <gift [card to be gifted] [receiving member]" )
async def gift(ctx, member: discord.Member, othermember: discord.Member=None):
    print("gift command called with", member.name, othermember)
    adminrole = discord.utils.get(ctx.guild.roles, name="admin")
    if ((not adminrole) and othermember):
        await ctx.send("Not an admin, you don't have permissions for this action.")
    else:
        if (adminrole and othermember):
            receivingmember = othermember
            cardgifted = member
        else:
            receivingmember = member
            cardgifted = ctx.author
        stats, _ = newcard.getstats(cardgifted.id)
        if not stats:
            await ctx.send("That member doesn't have enough points yet!")
        else:
            if not verifycard(cardgifted.id):
                createcard(cardgifted.id)
            results = verifyhascard(receivingmember.id, cardgifted.id)
            if results:
                results = results[0][0]
                executesql(DB_PATH, f"UPDATE memberhas SET quantity = {int(results)+1 if results > 0 else -1} WHERE memberid={receivingmember.id} AND cardid={cardgifted.id}")
            else:
                executesql(DB_PATH, f"INSERT INTO memberhas (memberid, cardid, quantity) VALUES ({receivingmember.id}, {cardgifted.id}, 1)")
            await ctx.send(f"Gifted {cardgifted.nick if cardgifted.nick else cardgifted.name}'s card to {receivingmember.nick if receivingmember.nick else receivingmember.name}")
    
@bot.command(name="searchcard", help="Searches for cards in your inventory. Usage: <searchcard [keywords]")
async def searchcard(ctx, keyword=None):
    if keyword: keyword = keyword.lower()
    results = executesql(DB_PATH, f"SELECT cardid, quantity FROM memberhas WHERE memberid={ctx.author.id}")
    if not results:
        if newcard.getstats(ctx.author.id):
                createcard(ctx.author.id)
                results = executesql(DB_PATH, f"SELECT cardid, quantity FROM memberhas WHERE memberid={ctx.author.id}")
        else: 
                await ctx.send("You don't have any cards yet!")
                return
    else: 
        options = []
        info = dict()
        for (cardid, quantity) in results:
            user = discord.utils.get(ctx.guild.members, id=cardid)
            if (not keyword) or (keyword in str(user.name).lower()) or (keyword in str(user.nick).lower()):
                name = user.nick if user.nick else user.name
                if quantity != 0:
                    options.append(discord.SelectOption(label=name, description=f"Quantity: {'Unlimited' if quantity == -1 else quantity}"))
                    info[name] = user
        if not options: await ctx.send("No results found...check your input or try more generic keywords!")
        else:
            selectmenu = Select(options, info, ctx.author)
            print(SelectView(select=selectmenu))
            await ctx.send("Here are the results we found:",view=SelectView(select=selectmenu))


@bot.command(name="update", help="Updates the database to create cards for people who don't have them but should have them. Admins only", category="Admins only")
async def update(ctx):
    adminrole = discord.utils.get(ctx.guild.roles, name="admin")
    if adminrole not in ctx.author.roles:
        await ctx.send("Not an admin, you are not authorised to perform this action.")
    else:
        allmembers = discord.utils.get(ctx.guild.members)
        for member in allmembers:
            stats, _ = newcard.getstats(member.id)
            if stats:
                if not verifycard(member.id):
                    createcard(member.id)
                    await ctx.send(f"Created {member.nick if member.nick else member.name}'s card!")

@bot.command(name="trade", help="Initiates a trade of cards. Usage: <trade [card offered by you] [card you want to receive]")
async def trade(ctx, cardoffered: discord.Member, cardreceived: discord.Member):
    memberhas = executesql(DB_PATH, f"SELECT cardid, quantity FROM memberhas WHERE memberid = {ctx.author.id}")
    print(memberhas)
    if not memberhas:
        await ctx.send("You don't have any cards yet!")
        return
    elif cardoffered.id not in [_[0] for _ in memberhas]:
        await ctx.send("You don't have that card yet!")
        return
    else:
        curquantity = 0
        for (cardid, quantity) in memberhas:
            if (cardid == cardoffered.id) and ((quantity != -1) and (quantity <= 0)):
                await ctx.send("You don't have enough of that card yet!")
                return
            elif (cardid == cardoffered.id):
                curquantity = quantity
    stats, _ = newcard.getstats(cardreceived.id)
    if not stats:
        await ctx.send("The card you are trying to obtain doesn't exist yet!")
        return
    else:
        if not verifycard(cardreceived.id):
            createcard(cardreceived.id)
            await ctx.send(f"Created {cardreceived.nick if cardreceived.nick else cardreceived.name}'s card!")
    results = executesql(DB_PATH, f"INSERT INTO trades (initmemberid, cardoffered, cardreceived, status) VALUES ({ctx.author.id}, {cardoffered.id}, {cardreceived.id}, False)")
    tradeid = executesql(DB_PATH, f"SELECT tradeid FROM trades WHERE (initmemberid = {ctx.author.id}) AND (cardoffered = {cardoffered.id}) AND (cardreceived = {cardreceived.id})")
    if cardoffered.id != ctx.author.id:
        results = executesql(DB_PATH, f"UPDATE memberhas SET quantity = {curquantity - 1} WHERE (memberid = {ctx.author.id}) AND (cardid = {cardoffered.id})")
    tradeid = max([trade[0] for trade in tradeid])
    await ctx.send("Created trade with id " + str(tradeid))

@bot.command(name="tradeaccept", help="Accepts a currently open trade. Usage: <tradeaccept [trade id]")
async def tradeaccept(ctx, tradeid):
    tradedetails = executesql(DB_PATH, f"SELECT initmemberid, cardoffered, cardreceived, status FROM trades WHERE tradeid = {tradeid}")
    if not tradedetails:
        await ctx.send("That trade doesn't exist!")
        return
    elif tradedetails[0][3]:
        await ctx.send("That trade has already been accepted!")
        return
    else:
        memberhas = executesql(DB_PATH, f"SELECT cardid, quantity FROM memberhas WHERE memberid = {ctx.author.id}")
        if not memberhas:
            await ctx.send("You don't have any cards yet!")
            return
        elif tradedetails[0][2] not in [_[0] for _ in memberhas]:
            await ctx.send("You don't have that card yet!")
            return
        else:
            alrquantity = 0
            givingquantity = 0
            for (cardid, quantity) in memberhas:
                if (cardid == tradedetails[0][2]):
                    givingquantity = quantity
                    if (givingquantity != -1) and (givingquantity <= 0):
                        await ctx.send("You don't have enough of that card yet!")
                        return
                elif (cardid == tradedetails[0][1]):
                    alrquantity = quantity
            results = executesql(DB_PATH, f"UPDATE trades SET status = True, acceptmemberid = {ctx.author.id} WHERE tradeid = {tradeid}")
            await ctx.send("Trade " + str(tradeid) + " complete!")
            results = executesql(DB_PATH, f"UPDATE memberhas SET quantity = {givingquantity - 1 if givingquantity != -1 else -1} WHERE (memberid = {ctx.author.id}) AND (cardid = {tradedetails[0][2]})")
            if alrquantity and alrquantity != -1:
                results = executesql(DB_PATH, f"UPDATE memberhas SET quantity = {alrquantity + 1} WHERE (memberid = {ctx.author.id}) AND (cardid = {tradedetails[0][1]})")
            else:
                results = executesql(DB_PATH, f"INSERT INTO memberhas (memberid, cardid, quantity) VALUES ({ctx.author.id}, {tradedetails[0][1]}, 1)")
            othermemberhas = executesql(DB_PATH, f"SELECT quantity FROM memberhas WHERE (memberid = {tradedetails[0][0]}) AND (cardid = {tradedetails[0][2]})")
            if not othermemberhas:
                newquantity = 0
            elif othermemberhas[0][0] == -1:
                newquantity = -1
            else:
                newquantity = othermemberhas[0][0]
            if newquantity:
                results = executesql(DB_PATH, f"UPDATE memberhas SET quantity = {newquantity + 1 if newquantity != -1} WHERE (memberid = {tradedetails[0][0]}) AND (cardid = {tradedetails[0][2]})")
            else:
                results = executesql(DB_PATH, f"INSERT INTO memberhas (memberid, cardid, quantity) VALUES ({tradedetails[0][0]}, {tradedetails[0][2]}, 1)")
            
@bot.command(name="viewtrades", help="Views trades with page >= 1. Usage: <viewtrades [page]")
async def viewtrades(ctx, page=None):
    if not page: page = 1
    try: page = int(page)
    except:
        await ctx.send("Invalid page.")
        return
    if (page < 1):
        await ctx.send("Invalid page.")
        return
    tradedetails = executesql(DB_PATH, f"SELECT * FROM trades WHERE (tradeid >= {(page-1)*10}) AND (tradeid <= {page*10})")
    await ctx.send(f"Listing trades from ID {(page-1)*10} to {page*10}:")
    for entry in tradedetails:
        st = gentradedetails(ctx, entry)
        await ctx.send(st)

@bot.command(name="gettrade", help="Gets a specific trade by id. Usage: <gettrade [id]")
async def gettrade(ctx, id):
    if not id:
        await ctx.send("Invalid id.")
        return
    try: id = int(id)
    except:
        await ctx.send("Invalid id.")
        return
    tradedetails = executesql(DB_PATH, f"SELECT * FROM trades WHERE tradeid = {id}")
    if not tradedetails:
        await ctx.send("Invalid id.")
        return
    await ctx.send(gentradedetails(ctx, tradedetails[0]))
        

def gentradedetails(ctx, entry):
    st = f"ID: {entry[0]}\n"
    initmem = discord.utils.get(ctx.guild.members, id=entry[1])
    cardoffered = discord.utils.get(ctx.guild.members, id=entry[2])
    cardreceived = discord.utils.get(ctx.guild.members, id=entry[3])
    st += f"Initiating member: {initmem.nick if initmem.nick else initmem.name}\n"
    st += f"Card offered: {cardoffered.nick if cardoffered.nick else cardoffered.name}'s card\n"
    st += f"Card received: {cardreceived.nick if cardreceived.nick else cardreceived.name}'s card\n"
    st += f"Status: {'Accepted' if entry[4] else 'Open'}\n"
    if entry[4]:
        acceptmem = discord.utils.get(ctx.guild.members, id=entry[5])
        st += f"Accepting member: {acceptmem.nick if acceptmem.nick else acceptmem.name}"
    st += "\n"
    return st


        




bot.run(TOKEN)