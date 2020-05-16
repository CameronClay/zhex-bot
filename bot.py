# bot.py
from Team import Team
import threading
import os
import random
from PlayerDB import PlayerDB
from Game import Game, State
from Player import Player, MatchRes
import threading
import itertools

#from discord import utilis
import discord
import functools
from discord.ext import commands
from dotenv import load_dotenv

#from threading import Thread, Lock

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='!')
guild = None

REG_NA = 'NA'
REG_EU = 'EU'
REG_ALL = 'ALL'
queues = {REG_NA: set(), REG_EU: set()}
games = {REG_NA: None, REG_EU: None}
REGIONS = [k for k, _ in queues.items()]
playerDB = PlayerDB()

pickTimedOut = False
def PickTimeout():
    global pickTimedOut
    with cvTimer:
        pickTimedOut = True
        cvTimer.notify()
    #asyncio.run(PickTimeoutHelper(ctx, game))

TIME_TO_PICK = 5
cvTimer = threading.Condition()
pickTimer = threading.Timer(TIME_TO_PICK, PickTimeout)

async def StartTeamPick(ctx, region):
    queue = queues[region]
    game = games[region] = Game(region, {playerDB.Find(id, region) for id in queue})
    queue = queues[region].clear()

    await ShowTeamPickInfo(ctx, game)
    await StartPickTimer(ctx, game)
    

async def ShowTeamPickInfo(ctx, game):
    players = IdsToNames(game.PoolIds)
    embed = discord.Embed(title=f'Picking teams on {game.region}', description=f'Zerg Captain: {IdToName(game.zergCapt.id)} | Terran Captain: {IdToName(game.terranCapt.id)}')
    embed.add_field(name=f"{IdToName(IdToName(game.playerTurn.id))}'s pick", value=f'players={players}')
    await ctx.channel.send(content=None, embed=embed)

def ResetPickTimer(ctx, game):
    global pickTimer
    global pickTimedOut

    pickTimedOut = False
    if pickTimer.is_alive():
        pickTimer.cancel()

    pickTimer = threading.Timer(TIME_TO_PICK, PickTimeout, [])

#need to set condition variable in other thread
async def StartPickTimer(ctx, game):
    ResetPickTimer(ctx, game)

    if game.state != State.IN_GAME:
        pickTimer.start()
        with cvTimer:
            cvTimer.wait()
            if pickTimedOut:
                await PickTimeoutHelper(ctx, game)
    else:
        await PickShow(ctx, game)

def IdToName(id):
    found = discord.utils.find(lambda player: player.id == id, bot.users)
    if found == None:
        return str(id)

    return bot.get_user(id).name

def IdsToNames(ids):
    return [IdToName(id) for id in ids]

#mutex = Lock()

@bot.event
async def on_ready():
    global guild
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(f'{bot.user.name} has connected to Discord!')
    
@bot.command(name='add', help='Add to queue (NA/EU/ALL)')
@commands.cooldown(2, 30)
async def on_add(ctx, region='ALL'):
    player = ctx.message.author.name
    playerId = ctx.message.author.id
    if not await CheckIsRegisterd(ctx):
        return

    if region == REG_ALL:
        for reg in REGIONS:
            #if player not in queues[reg]:
            if not any((games[newReg] != None and games[newReg].IsPlaying(playerId) for newReg in REGIONS)): #necessary if a player causes a game to start and queued on both regions
                await on_add(ctx, reg)
        return
                
    if region in REGIONS:
        if True: #playerId not in queues[region]:
            queues[region].add(playerId)
            #mutex.acquire()
            #try:
            #finally:
            #    mutex.release()
            #print(f'error!')
            await ctx.send(f'{player} added to {region} {len(queues[region])}/{Game.N_PLAYERS}')

            if len(queues[region]) == Game.N_PLAYERS:
                await StartTeamPick(ctx, region)
        else:
            await ctx.send(f'{player} already added to {region}')
    else:
        await ctx.send('Invalid region, expected: ' + '/'.join(REGIONS))
        return

@bot.command(name='rem', help='Remove from current queues')
@commands.cooldown(2, 30)
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

    if not await CheckIsRegisterd(ctx):
        return

    if len(pickedIds) != 1:
        await ctx.send(f'Must pick only 1 player')
        return
          
    region = RegFromPlayer(choosingId)
    if region == None:
        await ctx.send(f'Must be a captain in order to pick')
        return

    #if choosingId == pickedId:
    #    await ctx.send(f'Cannot pick self')
    #    return

    game = games[region]
    if game.playerTurn.id != choosingId:
        await ctx.send(f'Not your turn to pick')
        return

    if game.state == State.IN_GAME:
        await ctx.send(f'Game already running')
        return

    #if pickedId not in game.PoolIds():
    #    await ctx.send(f"Player not currently playing")
    #    return

    game.PickPlayer(pickedId)

    await ctx.send(f'{pickedPlayer} added to {game.PlayerRace(pickedId)}')
    await PickShow(ctx, game)

async def PickShow(ctx, game):
    if game.state == State.IN_GAME:
        await StartGame(ctx, game)
    else:
        await ShowTeamPickInfo(ctx, game)

@bot.command(name='rw', help='Captain report win')
@commands.cooldown(2, 30)
async def on_report_win(ctx):
    await ReportMatchResult(ctx, MatchRes.WIN)

@bot.command(name='rl', help='Captain report loss')
@commands.cooldown(2, 30)
async def on_report_loss(ctx):
    await ReportMatchResult(ctx, MatchRes.LOSS)

@bot.command(name='reg', help='Register with the server to play private games')
async def on_register(ctx):
    playerId = ctx.message.author.id
    playerName = ctx.message.author.name

    if playerDB.IsRegistered(playerId):
        await ctx.send(f'Already registered')
        return

    for reg in REGIONS:
        playerDB.Register(Player(playerId, reg))
    await ctx.send(f'Registration successful')

@bot.command(name='unreg', help='Register with the server to play private games')
@commands.has_role('MOD')
async def on_unregister(ctx, mention):
    players = ctx.message.mentions
    for player in players:
        playerDB.UnRegister(player.id)
        await ctx.send(f'{player.name} successfully unregistered')

@bot.command(name='stats', help='Retreive stats of player (name or mention)')
@commands.cooldown(2, 30)
#@commands.check(can_pick)
async def on_stats(ctx, name):
    trigPlayer = ctx.message.author.id
    players = ctx.message.mentions
    if not await CheckIsRegisterd(ctx):
        return
    if len(players) == 0:
        p = guild.get_member_named(name)
        if p == None:
            await ctx.send(f'Player {name} not registered')
            return
        players.append(p)

    for player in players:
        playerName = player.name

        embed = discord.Embed(title=f"Stats {playerName}")
        for region in REGIONS:
            usPlayer = playerDB.Find(player.id, region)
            if usPlayer:
                embed.add_field(name=region, value=f"Games: {usPlayer.games}\t Wins: {usPlayer.wins}\t Loses: {usPlayer.loses}\t \
                    Elo: {int(usPlayer.elo)}, Last played: {usPlayer.lastPlayed}")
        await ctx.channel.send(content=None, embed=embed)

@bot.command(name='status', help='Query status of queue and any running games')
@commands.cooldown(2, 30)
async def on_status(ctx):
    if not await CheckIsRegisterd(ctx):
        return

    for region, queue in queues.items():
        queued = IdsToNames(queue)
        embed = discord.Embed(title=f"Status of running/queued games on {region}", description=f"{len(queue)}/{Game.N_PLAYERS}\n Players: {queued}")
        if games[region] != None:
            zerg = IdsToNames(games[region].zerg.Ids)
            terran = IdsToNames(games[region].terran.Ids)
            embed.add_field(name="Running", value=f"Zerg: {zerg}\n Terran: {terran}")
        await ctx.channel.send(content=None, embed=embed)

@bot.command(name='setelo', help='Test command')
async def set_elo(ctx, mentions, region, elo : float):
    players = ctx.message.mentions

    for player in players:
        playerName = player.name

        usPlayer = playerDB.Find(player.id, region)
        if usPlayer == None:
            await ctx.send(f'Player {playerName} not registered')

        usPlayer.elo = elo
        playerDB.UpdateStats(usPlayer)
        await ctx.send(f"Updated {playerName}'s' elo to {usPlayer.elo}")

def RegFromPlayer(playerId):
    for reg, game in games.items():
        if game != None and game.CaptOnTeam(playerId):
            return reg

    return None

async def PickTimeoutHelper(ctx, game):
    await ctx.send(f'{IdToName(game.playerTurn.id)} took too long...')
    pickedPlayer = game.PickAfk()
    await ctx.send(f'{IdToName(pickedPlayer.id)} added to {game.PlayerRace(pickedPlayer.id)}')
    await StartPickTimer(ctx, game)


async def CheckIsRegisterd(ctx):
    if not playerDB.IsRegistered(ctx.message.author.id):
        await ctx.send(f'Must be registered to execute this command')
        return False
    
    return True

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
        
    oldZElo = [(IdToName(player.id), int(player.elo)) for player in game.zerg.players]
    oldTElo = [(IdToName(player.id), int(player.elo)) for player in game.terran.players]
    game.MatchResult(playerId, res)
    for player in itertools.chain(game.zerg.players, game.terran.players):
        playerDB.UpdateStats(player)

    newZElo = [(IdToName(player.id), int(player.elo)) for player in game.zerg.players]
    newTElo = [(IdToName(player.id), int(player.elo)) for player in game.terran.players]

    embed = discord.Embed(title=f"Match Concluded on {game.region}", description=f"Victor: {game.GetVictor(playerId, res)}")
    embed.add_field(name="Prior Elo's", value=f"Zerg: {oldZElo}\n Terran: {oldTElo}")
    embed.add_field(name="Updated Elo's", value=f"Zerg: {newZElo}\n Terran: {newTElo}")
    await ctx.channel.send(content=None, embed=embed)

    games[region] = None

async def StartGame(ctx, game):
    embed = discord.Embed(title=f"Game Starting on {game.region}", description=f"Start a prepicked lobby and arrange teams, captains report back the result of the game with rw/rl")
    zerg = IdsToNames(game.zerg.Ids)
    terran = IdsToNames(game.terran.Ids)
    embed.add_field(name="Teams", value=f"Zerg: {zerg}\n Terran: {terran}")
    await ctx.channel.send(content=None, embed=embed)

if __name__ == "__main__":
    stubIds = [i for i in range(1, 2 + 1)]
    for id in stubIds:
        if not playerDB.IsRegistered(id):
            playerDB.Register(Player(id, REG_NA))
        queues[REG_NA].add(id)

    bot.run(TOKEN)
    playerDB.Close()

    #guild = discord.utils.get(bot.guilds, name=GUILD)
    #print(
    #    f'{bot.user} is connected to the following guild:\n'
    #    f'{guild.name}(id: {guild.id})'
    #)