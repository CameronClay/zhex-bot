import Region
import itertools
from datetime import datetime

import discord
from discord.ext import commands, tasks
import asyncio
from PlayerDB import PlayerDB
from Game import Game, State
from Player import Player, MatchRes
from Utility import CodeB, CodeSB
from PQueue import PQueue

class Model(commands.Cog):  
    TIME_TO_PICK = 5  #in seconds
    #TIME_TO_PICK = 60  #in seconds
    QUEUE_TIMEOUT = 60 # in minutes
    QUEUE_TIMEOUT_EV = 5 # in minnutes
    PRIV_CHAN_ID = 710245665896398899
    PRIV_CAT_ID = 711399900008415232

    def __init__(self, TOKEN, GUILD):
        self.TOKEN = TOKEN
        self.GUILD = GUILD
        self.guild = None

        #self.queues = {Region.NA: set(), Region.EU: set()}
        #self.queues = {reg:set() for reg in Region.REGIONS}
        self.queues = PQueue()
        self.games = {reg:None for reg in Region.REGIONS}
        self.subs = {reg:set() for reg in Region.REGIONS}

        self.playerDB = PlayerDB()
        self.category = None
        self.privChannel = None
        self.autoPickTasks = dict()
        self.privVChannels = dict()
        self.evInit = asyncio.Event()
    
    def __enter__(self):
        self.bot = commands.Bot(command_prefix='!', help_command=commands.DefaultHelpCommand(command_attrs=dict(name='help-hex', aliases=['hex_help', 'help_hex', 'hex-help'])))
        self.pick_timeout.start()

    def cog_unload(self):
        self.cleanup()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def cleanup(self):
        self.pick_timeout.cancel()
        self.playerDB.Close()

    def run(self):
        self.bot.run(self.TOKEN)

    #async def reset(self):
    #    self.bot.clear()
    #    await self.bot.wait_until_ready()

    @tasks.loop(minutes=QUEUE_TIMEOUT_EV)
    async def pick_timeout(self):
        remQueues = dict()
        for reg, queue in self.queues:
            for id, timeQueued in queue.copy().items():
                timeDelta = (datetime.now() - timeQueued).total_seconds() / 60.0
                if timeDelta > Model.QUEUE_TIMEOUT:
                    self.queues.remove(reg, id)
                    playerName = self.IdToName(id)
                    remQueues.setdefault(playerName, [])
                    remQueues[playerName].append(reg)

        if len(remQueues) != 0:
            description = ""
            for playerName, regSet in remQueues.items():      
                description += f"-{playerName} timed out and removed from {', '.join(regSet)}\n"
            #description += f"\n\n{self.QueueStatus()}"
            embed = discord.Embed(colour = discord.Colour.blue(), description = CodeB(description, "diff"))
            await self.privChannel.send(content = CodeSB(self.QueueStatus()), embed = embed)
        #await self.privChannel.send( \
        #    content=f"{playerName} was queued over {Model.QUEUE_TIMEOUT:.1f} mins and was automatically removed from {', '.join(remQueues)}", embed=embed)
    
 
    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = discord.utils.get(self.bot.guilds, name=self.GUILD)
        self.privChannel = self.bot.get_channel(Model.PRIV_CHAN_ID)
        self.category = discord.utils.get(self.guild.categories, id=Model.PRIV_CAT_ID)

        print(f'{self.bot.user.name} is connected to {self.guild.name} (id: {self.guild.id})\n')   
        self.evInit.set()

    
    @pick_timeout.before_loop
    async def before_pick_timeout(self):
        await self.evInit.wait()
    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        with open('err.log', 'a') as f:
            if event == 'on_message':
                f.write(f'Unhandled message: {args[0]}\n')
            else:
                raise

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        #if isinstance(error, commands.errors.CheckFailure):
        #    await ctx.send(f'You do not have the correct role for this command')
        if isinstance(error, commands.errors.UserInputError) \
        or isinstance(error, commands.errors.ConversionError):
            syntax = f"Syntax: {ctx.prefix}{ctx.command.name} {ctx.command.signature}"
            await ctx.send(syntax)
        #elif isinstance(error, commands.errors.CommandNotFound):
        #    await ctx.send(f'Invalid command: "{ctx.invoked_with}"')


    def ChkIsReg(self, ctx):
        return self.ChkIsRegId(ctx.message.author.id)

    def ChkIsRegId(self, id):
        return self.playerDB.IsRegistered(id, Region.ALL)

    def RegFromPlayer(self, playerId):
        for reg, game in self.games.items():
            if game != None and game.CaptOnTeam(playerId):
                return reg

        return None
        
    def IdToUser(self, id):
        return self.guild.get_member(id)

    def IdToName(self, id):
        res = self.guild.get_member(id)
        if res == None:
            return str(id)

        return res.name
        #return bot.get_user(id).name

    def IdsToNames(self, ids):
        return ", ".join(self.IdToName(id) for id in ids)

    async def StartGame(self, ctx, game):
        self.subs[game.region].clear()
        embed = discord.Embed(title=f"Game Starting on {game.region}", description=f"Start a prepicked lobby and arrange teams, one captain report back the result of the game with rw/rl/rt")
        zerg = self.IdsToNames(game.zerg.Ids)
        terran = self.IdsToNames(game.terran.Ids)
        embed.add_field(name="Teams", value=f"Zerg: {zerg}\nTerran: {terran}")
        await ctx.channel.send(content=None, embed=embed)
        await self.CreateVoice(game)

    async def StartTeamPick(self, ctx, region):
        queue = self.queues[region]
        game = self.games[region] = Game(region, self.queues.to_players(region, self.playerDB))
        self.queues.clear(region)

        await self.ShowTeamPickInfo(ctx, game)
        await self.StartPickTimer(ctx, game)

    async def ShowTeamPickInfo(self, ctx, game):
        players = self.IdsToNames(game.PoolIds)
        embed = discord.Embed(title=f'Picking teams on {game.region}', \
            description=f'Zerg Captain: {self.IdToName(game.zergCapt.id)} | Terran Captain: {self.IdToName(game.terranCapt.id)}')
        embed.add_field(name=f"{self.IdToName(game.playerTurn.id)}'s pick", value=f'Player pool: {players}')
       
        zerg = self.IdsToNames(game.zerg.Ids)
        terran = self.IdsToNames(game.terran.Ids)
        embed.add_field(name="Teams", value=f"Zerg: {zerg}\n Terran: {terran}")
        await ctx.channel.send(content=None, embed=embed)

    async def PickShow(self, ctx, game):
        if game.state == State.IN_GAME:
            await self.StartGame(ctx, game)
        else:
            await self.ShowTeamPickInfo(ctx, game)

    async def PickTimerHelper(self, ctx, game):
        while True:
            await asyncio.sleep(Model.TIME_TO_PICK)
            #channel = discord.utils.find(lambda name: name == "General", self.guild.text_channels)
            pickedPlayer = game.PickAfk()

            await ctx.send(f'{self.IdToName(game.playerTurn.id)} ({game.PlayerRace(pickedPlayer.id)}) timed out and chose {self.IdToName(pickedPlayer.id)}')
            await self.PickShow(ctx, game)
            if game.state == State.IN_GAME:
                return

    async def StartPickTimer(self, ctx, game):
        if game.state != State.IN_GAME:
            await self.CancelPickTimer(game)
            self.autoPickTasks[game.region] = asyncio.create_task(self.PickTimerHelper(ctx, game))

    async def CancelPickTimer(self, game):
        if game.region in self.autoPickTasks:
            self.autoPickTasks[game.region].cancel()
            try:
                await self.autoPickTasks[game.region]
            except Exception:
                pass
            self.autoPickTasks.pop(game.region)

    async def ReportMatchResult(self, ctx, res, playerId):           
        region = self.RegFromPlayer(playerId)
        if region == None:
            await ctx.send(f'Must be a captain in order to report match result')
            return

        game = self.games[region]
        if game == None or game.state != State.IN_GAME:
            await ctx.send(f'Cannot report result of non-running game')
            return
            
        oldZElo = [(self.IdToName(player.id), int(player.elo)) for player in game.zerg.players]
        oldTElo = [(self.IdToName(player.id), int(player.elo)) for player in game.terran.players]
        game.MatchResult(playerId, res)
        for player in itertools.chain(game.zerg.players, game.terran.players):
            self.playerDB.UpdateStats(player)

        newZElo = [(self.IdToName(player.id), int(player.elo)) for player in game.zerg.players]
        newTElo = [(self.IdToName(player.id), int(player.elo)) for player in game.terran.players]

        embed = discord.Embed(title=f"Match Concluded on {game.region}", description=f"Victor: {game.GetVictor(playerId, res)}")
        #embed.add_field(name="Prior Zerg elo's", value=f"{oldTElo}")
        #zUpddElos = [(oldElo, newElo) for oldElo, newElo in zip(oldZElo, newZElo)]
        nameMax = max(len(name) for name, _ in oldZElo)
        strZUpdElos = '\n'.join([f'{oldElo[0].ljust(nameMax)}: {oldElo[1]} -> {newElo[1]}' for oldElo, newElo in zip(oldZElo, newZElo)])
        strTUpdElos = '\n'.join([f'{oldElo[0].ljust(nameMax)}: {oldElo[1]} -> {newElo[1]}' for oldElo, newElo in zip(oldTElo, newTElo)])
        
        embed.add_field(name="Updated Zerg elo's        ", value=strZUpdElos)
        embed.add_field(name="Updated Terran elo's      ", value=strTUpdElos)
        #embed.add_field(name="Prior elo's", value=f"Zerg: {oldZElo}\n Terran: {oldTElo}")
        #embed.add_field(name="Updated elo's", value=f"Zerg: {newZElo}\n Terran: {newTElo}")
        await ctx.channel.send(content=None, embed=embed)

        await self.DeleteVoice(game)
        self.games[region] =  None

    async def PickPlayer(self, ctx, game, choosingPlayer, pickedId, pickedPlayer):
        self.subs[game.region].discard(pickedId)
        game.PickPlayer(pickedId)
        await ctx.send(f'{choosingPlayer} ({game.PlayerRace(pickedId)}) chose {pickedPlayer}')
        await self.PickShow(ctx, game)
        await self.StartPickTimer(ctx, game)

    def CreateStubs(self, region, nStubs):
        if region == Region.ALL:
            for reg in Region.REGIONS:
                self.CreateStubs(reg, nStubs)
        else:
            stubIds = [i for i in range(1, nStubs + 1)]
            for id in stubIds:
                if not self.playerDB.IsRegistered(id, region):
                    self.playerDB.Register(Player(id, region))
                self.queues.add(region, id)

    async def CreateVoice(self, game):
        zergCaptName = self.IdToName(game.zergCapt.id)
        terranCaptName = self.IdToName(game.terranCapt.id)
        zChannelN = f"[{game.region}] {zergCaptName}"
        tChannelN = f"[{game.region}] {terranCaptName}"

        newChannels = set()
        zChannel = await self.guild.create_voice_channel(zChannelN, category = self.category, user_limit=Game.SIZE_ZERG)
        await self.SetVoicePerm(game.zerg.Ids, zChannel)
        newChannels.add(zChannel)

        tChannel = await self.guild.create_voice_channel(tChannelN, category = self.category, user_limit=Game.SIZE_TERRAN)
        await self.SetVoicePerm(game.terran.Ids, tChannel)
        newChannels.add(tChannel)

        self.privVChannels[game.region] = newChannels
        
        #newRoles = set()
        #zRole = self.guild.create_role(zChannelN)
        #newRoles.add(zRole)
#
        #tRole = self.guild.create_role(tChannelN)
        #newRoles.add(tRole)
        #await self.MoveUsers(game.zerg.Ids, zChannel)
        #await self.MoveUsers(game.terran.Ids, tChannel)

    async def SetVoicePerm(self, ids, channel):
        await channel.set_permissions(self.guild.default_role, \
            connect = False, speak = False)
        for id in ids:
            user = self.IdToUser(id)
            if user:
                await channel.set_permissions(user, connect = True, speak = True)

    async def DeleteVoice(self, game):
    #    await self.MoveUsers(itertools.chain(game.zerg.Ids, game.terran.Ids), self.privChannel)
        for channel in self.privVChannels[game.region]:
            await channel.delete()

    def QueueStatus(self):
        return " ".join(f'[{reg}] {len(self.queues[reg])}/{Game.N_PLAYERS}' for reg in Region.REGIONS)
        

    async def ValidateReg(self, ctx, region):
        if not Region.Valid(region):
            await ctx.send('Invalid region, expected: ' + '/'.join(Region.VALID_REGIONS))
            return False
        return True
    #async def MoveUsers(self, ids, channel):
    #    for id in ids:
    #        user = self.IdToUser(id)
    #        if user:
    #            user.voice = discord.VoiceState(True, channel = channel)

#async def MoveToVoice(ctx, game):
#    zChannel = f"{game.region} Zerg"
#    tChannel = f"{game.region} Terran"
#    for channel in [zChannel, tChannel]:
#        found = guild.fin
#    await guild.create_voice_channel(zChannel)
#    for id in game.zerg.Ids:
#        user = IdToUser(id)
#        if user:
#            user.move_to(zChannel)
#

    #def MoveToNewVoice(self, game):
    #    zergCaptName = self.IdToName(game.zergCapt.id)
    #    terranCaptName = self.IdToName(game.terranCapt.id)
    #    zChannel = f"Team {zergCaptName}"
    #    tChannel = f"Team {terranCaptName}"
    #    await guild.create_voice_channel(zChannel)
    #    await guild.create_voice_channel(zChannel)
#
    #    for ids in game.zerg.Ids:


    #async def PickTimeoutHelper(self, ctx, game):
    #    await self.bot.send(f'{self.IdToName(game.playerTurn.id)} took too long...')
    #    pickedPlayer = game.PickAfk()
    #    await self.bot.send(f'{self.IdToName(pickedPlayer.id)} added to {game.PlayerRace(pickedPlayer.id)}')
    #    await self.StartPickTimer(ctx, game)

    #@tasks.loop(seconds=10)
    #async def PickTimeoutEU(self):
    #    game = self.games[Region.EU]
    #    await self.PickTimerHelper(game)
#
    #def EnablePickTimer(self, region):       
    #    if region == Region.NA:
    #        self.PickTimeoutNA.start()
    #    elif region == Region.EU:
    #        self.PickTimeoutEU.restart()

    #def CancelPickTimer(self, region):
    #    if region == Region.NA:
    #        self.PickTimeoutNA.cancel()
    #    elif region == Region.EU:
    #        self.PickTimeoutEU.cancel()

    #def StartPickTimer(self)
                    
    #def ResetPickTimer(self, ctx, game):
        #self.pickTimedOut = False
        #if self.pickTimer.is_alive():
         #   self.pickTimer.cancel()

        #self.pickTimer = threading.Timer(Model.TIME_TO_PICK, Model.PickTimeout, [self])

    #need to set condition variable in other thread
    #async def StartPickTimer(self, ctx, game):
    #    self.ResetPickTimer(ctx, game)
#
    #    if game.state != State.IN_GAME:
    #        self.pickTimer.start()
    #        #with self.cvTimer:
    #        #    self.cvTimer.wait()
    #        #    if self.pickTimedOut:
    #        #await self.PickTimeoutHelper(ctx, game)
    #    else:
    #        await self.PickShow(ctx, game)
#
    #        #await MoveToVoice(ctx, game)