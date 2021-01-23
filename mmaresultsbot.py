import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import datetime

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
LIMIT = 60

waitTime = datetime.datetime(1999,1,1,1,1,1)

bot = commands.Bot(command_prefix="mmabot ")

def checkLimit():
    global waitTime
    now = datetime.datetime.now()
    if(waitTime <= now):
        return 0
    else:
        return 1

def enforceLimit():
    global waitTime
    now = datetime.datetime.now()
    waitTime = now + datetime.timedelta(seconds=LIMIT)
 
@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

@bot.command()
async def results(ctx):
    if(checkLimit()):
        await ctx.channel.send("Please wait before requesting results again")
        return
    event = ctx.message.content.split("mmabot results")[1].strip()
    searchTerm = event.replace(' ','+')
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        page = requests.get("https://www.tapology.com/search?term="+searchTerm+"&commit=Submit&model%5Bevents%5D=eventsSearch", headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')
    except:
        await ctx.channel.send("error searching that event")
        enforceLimit()
        return
    try:  
        eventFound = soup.find('table', class_="fcLeaderboard").find('td').find('a')
    except:
        await ctx.channel.send("couldn't find that event")
        enforceLimit()
        return
    try:    
        page = requests.get("https://www.tapology.com"+eventFound['href'], headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')
    except:
        await ctx.channel.send("error getting results")
        enforceLimit()
        return
    try:        
        fightCard = soup.find('h3', text="Fight Card").findNext('ul').findAll('li')
    except:
        await ctx.channel.send("no fight card found")
        enforceLimit()
        return
    
    output = "__"+eventFound.text+" Results__\n"
   
    for fight in fightCard:
        result = fight.find(class_="result")
        if not (result):
            result = "NONE"
        else:
            result = result.text.strip()
            result = result.split(',')[0]+"("+result.split(', ')[1]+")"
        
        fighterLeft = fight.find(class_="fightCardFighterName left")
        if not (fighterLeft):
            break
        fighterLeft = fighterLeft.text.strip()
        
        fighterRight = fight.find(class_="fightCardFighterName right")
        if not (fighterRight):
            break
        fighterRight = fighterRight.text.strip()
          
        time = fight.find(class_="time")
        if not(time):
            time = " "
        else:
            time = time.text.strip()
            
        if(result == "NONE"):
            output += (fighterLeft+" vs. "+fighterRight+"\n")
        elif(result.find("Draw") >= 0 or result.find("No Contest") >= 0):
            output += (fighterLeft+" vs. "+fighterRight+" "+result+"\n")
        elif(result.find("Decision") >= 0):
            output += (fighterLeft+" defeated "+fighterRight+" via "+result+"\n")
        else:
            time = time.split(' ')
            output += (fighterLeft+" defeated "+fighterRight+" via "+result+" at "+time[0]+" of "+time[1]+" "+time[2] +"\n")
    
    enforceLimit()
    await ctx.channel.send(output)
bot.run(TOKEN)