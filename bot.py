# bot.py
from Team import Team
import os
import random
from PlayerDB import PlayerDB
from Game import Game, State
from Player import Player, MatchRes

#from discord import utilis
import discord
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
queues = {REG_NA: [], REG_EU: []}
games = {REG_NA: None, REG_EU: None}
REGIONS = [k for k, _ in queues.items()]
playerDB = PlayerDB()

#mutex = Lock()

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    
@bot.command(name='add', help='Add to queue (NA/EU/ALL)')
async def on_add(ctx, region='ALL'):
    player = ctx.message.author.name
    player_id = ctx.message.author.id
    if region == REG_ALL:
        for reg in REGIONS:
            #if player not in queues[reg]:
            await on_add(ctx, reg)
        return
                
    if region in queues:
        if player not in queues[region]:
            queues[region].append(player_id)
            #mutex.acquire()
            #try:
            #finally:
            #    mutex.release()
            #print(f'error!')
            await ctx.send(f'{player} added to {region} {len(queues[region])}/{Game.N_PLAYERS}')

            if len(queues[region]) == Game.N_PLAYERS:
                StartTeamPick(ctx, region)
        else:
            await ctx.send(f'{player} already added to {region}')
    else:
        await ctx.send('Invalid region, expected: ' + '/'.join(REGIONS))
        return

@bot.command(name='rem', help='Remove from current queues')
async def on_remove(ctx):
    player = ctx.message.author.name

    for _,queue in queues.items():
        if player in queue:
            queue.remove(player)

    await ctx.send(f'{player} removed from all queues!')

@bot.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command')

#def can_pick(ctx):
#    return RegFromPlayer(ctx.message.author.id ) != None
        
@bot.command(name='pick', help='Pick @mention')
#@commands.check(can_pick)
async def on_pick(ctx, mention):
    choosingId = ctx.message.author.id
    pickedIds = ctx.message.mentions
    pickedId = pickedIds[0].id
    pickedPlayer = pickedIds[0].name

    if len(pickedIds) != 1:
        await ctx.send(f'Must pick only 1 player')
        return
          
    region = RegFromPlayer(choosingId)
    if region == None:
        await ctx.send(f'Must be a captain in order to pick')
        return

    if game.state == State.IN_GAME:
        await ctx.send(f'Game already running')
        return

    if choosingId == pickedId:
        await ctx.send(f'Cannot pick self')
        return

    game = games[region]
    if game.playerTurn != choosingId:
        await ctx.send(f'Not your turn to pick')
        return

    game.PickPlayer(pickedId)

    await ctx.send(f'{pickedPlayer} added to {game.CaptRace()}')

    if game.state == State.IN_GAME:
        StartGame(ctx, game)

@bot.command(name='rw', help='Captain report win')
async def on_report_win(ctx):
    await ReportMatchResult(ctx, MatchRes.WIN)

@bot.command(name='rl', help='Captain report loss')
async def on_report_loss(ctx):
    await ReportMatchResult(ctx, MatchRes.LOSS)

@bot.command(name='reg', help='Register with the server to play private games')
async def on_register(ctx):
    playerId = ctx.message.author.id
    playerName = ctx.message.author.name

    if playerDB.IsRegistered(playerId):
        await ctx.send(f'Already registered')
        return

    playerDB.Register(Player(playerId))
    await ctx.send(f'Registration successful')

@bot.command(name='unreg', help='Register with the server to play private games')
@commands.has_role('MOD')
async def on_unregister(ctx, mention):
    players = ctx.message.mentions
    for player in players:
        playerDB.UnRegister(player.id)
        await ctx.send(f'{player.name} successfully unregistered')

@bot.command(name='stats', help='Retreive stats of player')
#@commands.check(can_pick)
async def on_stats(ctx, mention):
    trigPlayer = ctx.message.author.id
    players = ctx.message.mentions

    for player in players:
        playerName = player.name
        usPlayer = playerDB.Find(player.id)
        if usPlayer == None:
            await ctx.send(f'Player {playerName} not registered')

        embed = discord.Embed(title="Stats", description=f"{playerName}")
        for region in REGIONS:
            embed.add_field(name=region, value=f"Games: {usPlayer.Games}\t Wins: {usPlayer.wins}\t Loses: {usPlayer.loses}\t Elo: {usPlayer.Elo}")
        await ctx.channel.send(content=None, embed=embed)

@bot.command(name='status', help='Query status of queue and any running games')
async def on_status(ctx):
    for region, queue in queues.items():
        embed = discord.Embed(title="Status", description=f"Status of running/queued games on {region}")
        queued = [bot.get_user(id).name for id in queue]
        embed.add_field(name="Queued", value=f"{len(queue)}/{Game.N_PLAYERS}\n Players: {queued}")
        if games[region] != None:
            zerg = games[region].ZergPlayers()
            terran = games[region].TerranPlayers()
            embed.add_field(name="Running", value=f"Zerg: {zerg}\n Terran: {terran}")
        await ctx.channel.send(content=None, embed=embed)

def RegFromPlayer(player):
    for reg, game in games.items():
        if game == None:
            return None
        if game.CaptOnTeam(player):
            return reg

    return None

async def StartTeamPick(ctx, region):
    await ctx.send(f'Picking teams on {region}, players={queues[region]}')
    game = games[region] = Game(region, queues[region])
    queues = queues[region].clear()

    await ctx.send(f'Zerg Captain: {game.zergCapt}, Terran Captain: {game.terranCapt}')

async def ReportMatchResult(ctx, res):
    playerId = ctx.message.author.id
          
    region = RegFromPlayer(playerId)
    if region == None:
        await ctx.send(f'Must be a captain in order to report match result')
        return

    game = games[region]
    if game == None or game.state != State.IN_GAME:
        await ctx.send(f'Cannot report result of non-running game')
        return

    game.MatchResult(playerId, res)

async def StartGame(ctx, game):
    embed = discord.Embed(title=f"Game Starting on {game.region}", description=f"Start a prepicked lobby and arrange teams, captains report back the result of the game with rw/rl")
    zerg = game.ZergPlayers()
    terran = game.TerranPlayers()
    embed.add_field(name="Players", value=f"Zerg: {zerg}\n Terran: {terran}")
    await ctx.channel.send(content=None, embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)
    playerDB.Close()

    #guild = discord.utils.get(bot.guilds, name=GUILD)
    #print(
    #    f'{bot.user} is connected to the following guild:\n'
    #    f'{guild.name}(id: {guild.id})'
    #)
