# bot.py
import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv

import newcard

print("imports successful")

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

# This example requires the 'message_content' intent.

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix="<", intents=intents)

@bot.command(name="add")
async def add(ctx, arg1, arg2):
    await ctx.send("The answer is " + str(int(arg1)+int(arg2)))

@bot.command(name="getpfp")
async def getpfp(ctx, member: discord.Member = None):
    if not member:
        member = ctx.author
    if not member.avatar:
        await ctx.send("Empty profile picture!")
    else:
        print(member.avatar)
        await ctx.send(member.avatar)

@bot.command(name="mycard")
async def mycard(ctx, member: discord.Member = None):
    if not member:
        member = ctx.author
    print(member.name)
    print(member.id)
    print(member.avatar)
    stats, pos = newcard.getstats(member.id)
    nat = "gb"
    quote = "I am a honorary German."
    newcard.newcard(member.name, stats, pos, nat, quote, member.avatar, "cards/" + member.name + ".png")

    await ctx.send("done")

bot.run(TOKEN)