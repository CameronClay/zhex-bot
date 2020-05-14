# bot.py
from Team import Team
import os
import random
from Game import Game

#from discord import utilis
from discord.ext import commands
from dotenv import load_dotenv

#from threading import Thread, Lock

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='!')

REG_NA = 'NA'
REG_EU = 'EU'
REG_ALL = 'ALL'
N_PLAYERS = 8
queues = {REG_NA: [], REG_EU: []}
games = {REG_NA: None, REG_EU: None}
REGIONS = [k for k, _ in queues.items()]

#mutex = Lock()

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    
@bot.command(name='add', help='Add to queue (NA/EU/ALL)')
async def OnAdd(ctx, region='ALL'):
    player = ctx.message.author.name
    if region == REG_ALL:
        for reg in REGIONS:
            #if player not in queues[reg]:
            await OnAdd(ctx, reg)
        return
                
    if region in queues:
        if player not in queues[region]:
            queues[region].append(player)
            #mutex.acquire()
            #try:
            #finally:
            #    mutex.release()
            #print(f'error!')
            await ctx.send(f'{player} added to {region} {len(queues[region])}/{N_PLAYERS}')

            if len(queues[region]) == N_PLAYERS:
                StartTeamPick(ctx, region)
        else:
            await ctx.send(f'{player} already added to {region}')
    else:
        await ctx.send('Invalid region, expected: ' + '/'.join(REGIONS))
        return

@bot.command(name='rem', help='Remove from current queues')
async def OnRemove(ctx):
    player = ctx.message.author.name

    for _,queue in queues.items():
        if player in queue:
            queue.remove(player)

    await ctx.send(f'{player} removed from all queues!')

@bot.event
async def OnError(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise

@bot.event
async def OnCommandError(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')

        
@bot.command(name='pick', help='Pick @mention')
async def OnPick(ctx, mention):
    player = ctx.message.author.name
    region = RegFromPlayer(player)
    if region == None:
        await ctx.send(f'Unable to pick player {player}')
        return

    games[region].PickPlayer(player)

    await ctx.send(f'{player} added to {games[region].CaptRace()}')

@bot.command(name='status', help='Query status of queue and any running games')
async def OnStatus(ctx, mention):
    None

def RegFromPlayer(player):
    for reg, game in games.items():
        if game == None:
            return None
        if game.CaptOnTeam(player):
            return reg

    return None

async def StartTeamPick(ctx, region):
    await ctx.send(f'Picking teams on {region}, players={queues[region]}')
    games[region] = Game(region, queues[region])
    queues = queues[region].clear()

    await ctx.send(f'Captains: {games[region].captain1}, {games[region].captain2}')

if __name__ == "__main__":
    bot.run(TOKEN)

    #guild = discord.utils.get(bot.guilds, name=GUILD)
    #print(
    #    f'{bot.user} is connected to the following guild:\n'
    #    f'{guild.name}(id: {guild.id})'
    #)
