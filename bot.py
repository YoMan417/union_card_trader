# bot.py
import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv
import sqlite3
from PIL import Image

import newcard

print("imports successful")

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DB_PATH = GUILD + "_cards.db"

# This example requires the 'message_content' intent.

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix="<", intents=intents)

def executesql(db_path, query, close=True):
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        db.commit()
    if close:
        cursor.close()
    return result

def createcard(dsc_id):
    executesql(DB_PATH, f"INSERT INTO members VALUES ({dsc_id}, '', '', FALSE)")

def verifycard(dsc_id):
    results = executesql(DB_PATH, f"SELECT 1 FROM members WHERE memberid = {dsc_id}")
    return (True if results else False)

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
        return f"Set {ctx.author.name}'s {attr} to {arg}!"
    

@bot.command(name="mycard")
async def mycard(ctx, member: discord.Member = None):
    adminrole = discord.utils.get(ctx.guild.roles, name="admin")
    if not member:
        member = ctx.author
    stats, pos = newcard.getstats(member.id)
    if not stats:
        await ctx.send("You don't have enough points yet! Get 5,000 points for UNION to get your own card!")
        return 
    else:
        if not verifycard(member.id):
            createcard(member.id)
        results = executesql(DB_PATH, f"SELECT nation, quote, public FROM members WHERE members.memberid = {member.id}")[0]
        print(results)
        print(member.nick, member.name, member)

        if ((str(results[2]) == "0") and (member != ctx.author)):
            if (adminrole not in ctx.author.roles):
                await ctx.send("That member's card is private. Ask them for a trade or defeat them in a 1v1 battle to get their card!")
                return
            else:
                await ctx.send("Bypassing privacy with admin role...")
        nat = results[0]
        quote = results[1]
        name = member.nick if member.nick else member.name
        img, stat = newcard.newcard(name, stats, pos, member.avatar, "cards/" + member.name + ".png", nat, quote)
        if not stat:
            await ctx.send("That flag does not currently exist in the database.")
        path = "tmp/card.png"
        img.save(path)
        await ctx.send("", file=discord.File(path))

bot.run(TOKEN)