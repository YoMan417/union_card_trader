# bot.py
import os
import random

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
            await interaction.response.send_message(content=f"Displaying {self.values[0]}'s card",embed=embed, file=file ,ephemeral=True)

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

@bot.command(name="init")
async def init(ctx, member: discord.Member = None):
    if not member:
        member = ctx.author
    role = discord.utils.get(ctx.guild.roles, name="admin")
    if role not in member.roles:
        await ctx.send("Not an admin, you are not authorised to perform this command.")
        return 
    else:
        if not os.path.isfile(DB_PATH):
            sqlite3.connect(DB_PATH)
            executesql(DB_PATH, "CREATE TABLE IF NOT EXISTS members (memberid INTEGER PRIMARY KEY, nation STRING, quote STRING, public STRING)")
            print("1 created")
            executesql(DB_PATH, "CREATE TABLE IF NOT EXISTS memberhas (membercardid INTEGER PRIMARY KEY AUTOINCREMENT, memberid INTEGER, cardid INTEGER, quantity INTEGER)")
            print('2 created')
            executesql(DB_PATH, "CREATE TABLE IF NOT EXISTS trades (tradeid INTEGER PRIMARY KEY AUTOINCREMENT, initmemberid INTEGER, cardoffered INTEGER, cardrequired INTEGER, status BOOLEAN, acceptmemberid INTEGER)")
    await ctx.send("Initialisation successful for " + GUILD)

@bot.command(name="setpublic")
async def setpublic(ctx, member: discord.Member = None):
    if member == None:
        msg = setattr(ctx, "public", "1")
    else:
        msg = setattr(ctx, "public", member, "1")
    await ctx.send(msg)

@bot.command(name="setprivate")
async def setprivate(ctx, member: discord.Member = None):
    if member == None:
        msg = setattr(ctx, "public", "0")
    else:
        msg = setattr(ctx, "public", member, "0")
    await ctx.send(msg)

@bot.command(name="setnation")
async def setnation(ctx, arg, optional=None):
    if arg.isalpha():
        arg = arg.lower()
    elif optional.isalpha():
        optional = optional.lower()
    msg = setattr(ctx, "nation", arg, optional)
    await ctx.send(msg)

@bot.command(name="setquote")
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
    
@bot.command(name="gift")
async def gift(ctx, member: discord.Member, othermember: discord.Member=None):
    print("gift command called with", member.name, othermember)
    adminrole = discord.utils.get(ctx.guild.roles, name="admin")
    if ((not adminrole) and othermember):
        await ctx.send("Not an admin, you don't have permissions for this action.")
    else:
        if (adminrole and othermember):
            receivingmemberid = othermember.id
            cardgiftedid = member.id
        else:
            receivingmemberid = member.id
            cardgiftedid = ctx.author.id
        stats, _ = newcard.getstats(cardgiftedid)
        if not stats:
            await ctx.send("That member doesn't have enough points yet!")
        else:
            if not verifycard(cardgiftedid):
                createcard(cardgiftedid)
            results = verifyhascard(receivingmemberid, cardgiftedid)
            print(results)
            if results:
                results = results[0][0]
                executesql(DB_PATH, f"UPDATE memberhas SET quantity = {int(results)+1} WHERE memberid={receivingmemberid} AND cardid={cardgiftedid}")
            else:
                executesql(DB_PATH, f"INSERT INTO memberhas (memberid, cardid, quantity) VALUES ({receivingmemberid}, {cardgiftedid}, 1)")
            await ctx.send(f"Gifted {member.nick if member.nick else member.name}'s card to {othermember.nick if othermember.nick else othermember.name}")
    
@bot.command(name="searchcard")
async def searchcard(ctx, keyword=None):
    if keyword: keyword = keyword.lower()
    results = executesql(DB_PATH, f"SELECT cardid, quantity FROM memberhas WHERE memberid={ctx.author.id}")
    if not results: 
        await ctx.send("You don't have any cards yet!")
        return
    else: 
        options = []
        info = dict()
        for (cardid, quantity) in results:
            user = discord.utils.get(ctx.guild.members, id=cardid)
            if (not keyword) or (keyword in str(user.name).lower()) or (keyword in str(user.nick).lower()):
                name = user.nick if user.nick else user.name
                options.append(discord.SelectOption(label=name, description=f"Quantity: {quantity}"))
                info[name] = user
        if not options: await ctx.send("No results found...check your input or try more generic keywords!")
        else:
            selectmenu = Select(options, info, ctx.author)
            print(SelectView(select=selectmenu))
            await ctx.send("Here are the results we found:",view=SelectView(select=selectmenu))


@bot.command(name="update")
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




bot.run(TOKEN)