from Region import Region
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
    TIME_TO_PICK = 90  #in seconds
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
        self.privVChannelIds = dict()
        self.evInit = asyncio.Event()
    
    def __enter__(self):
        self.bot = commands.Bot(command_prefix='!', help_command=commands.DefaultHelpCommand(command_attrs=dict(name='help'), width=120, dm_help=True))#, aliases=['hex_help', 'help_hex', 'hex-help'])))
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
        if isinstance(error, commands.errors.ArgumentParsingError):
            await ctx.send(error)
        elif isinstance(error, commands.errors.UserInputError) \
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
    
    def IdToMention(self, id):
        member = self.guild.get_member(id)
        return member.mention if member else str(id)

    @staticmethod
    def UserToMention(member, id):
        return member.mention if member else f'@{id}'

    def IdToName(self, id):
        res = self.guild.get_member(id)
        if res == None:
            return str(id)

        return res.name
        #return bot.get_user(id).name

    @staticmethod
    def UserToName(member, id):
        return member.name if member else str(id)

    def IdsToNames(self, ids):
        return ", ".join(self.IdToName(id) for id in ids)

    def RemoveInGameFromQueue(self, game):
        for id in game.AllPlayers:
            self.queues.remove_all_of(Region.ALL, id)

    async def StartGame(self, ctx, game):
        zerg = [(self.IdToUser(id),id) for id in game.zerg.Ids]
        terran = [(self.IdToUser(id),id) for id in game.terran.Ids]

        zergNames = ", ".join(map(lambda memtup: Model.UserToName(memtup[0], memtup[1]), zerg))
        terranNames = ", ".join(map(lambda memtup: Model.UserToName(memtup[0], memtup[1]), terran))

        zergMentions = " ".join(map(lambda memtup: Model.UserToMention(memtup[0], memtup[1]), zerg))
        terranMentions = " ".join(map(lambda memtup: Model.UserToMention(memtup[0], memtup[1]), terran))

        description = f'''
One captain start a prepicked lobby and arrange teams and report back the result of the game with < !rw/!rl/!rt >

<Zerg> {zergNames}
<Terran> {terranNames}
'''
        embed = discord.Embed(description=CodeB(description, 'md'), colour = discord.Colour.blue())
        await ctx.channel.send(content=CodeSB(f"Game Starting on {game.region}") + f' {zergMentions} {terranMentions}', embed=embed)
        await self.CreateVoice(game)

    async def StartTeamPick(self, ctx, region):
        game = self.games[region] = Game(region, self.queues.return_players(region, self.playerDB))
        self.RemoveInGameFromQueue(game)

        await self.ShowTeamPickInfo(ctx, game, True)
        await self.StartPickTimer(ctx, game)

    async def ShowTeamPickInfo(self, ctx, game, pingCapts = False):
        playerPool = ', '.join(f'{self.IdToName(player.id)}({player.racePref.race})' for player in list(game.PoolPlayers))
        
        zCapt = self.IdToMention(game.zergCapt.id) if pingCapts else f"`{self.IdToName(game.zergCapt.id)}`"
        tCapt = self.IdToMention(game.terranCapt.id) if pingCapts else f"`{self.IdToName(game.terranCapt.id)}`"
        embed = discord.Embed(colour = discord.Colour.blue())
        embed.add_field(name=f"{self.IdToName(game.playerTurn.id)}'s pick", value=CodeB(f'<Pool> {playerPool}', 'md'))
       
        zerg = self.IdsToNames(game.zerg.Ids)
        terran = self.IdsToNames(game.terran.Ids)
        embed.add_field(name="Teams", value=CodeB(f"<Zerg> {zerg}\n<Terran> {terran}", 'md'))
        await ctx.channel.send(content=CodeSB(f'Picking teams on {game.region}') + f' - Captains - <Zerg> {zCapt} | <Terran> {tCapt}', embed=embed)

    async def PickShow(self, ctx, game):
        if game.state == State.IN_GAME:
            await self.StartGame(ctx, game)
        else:
            await self.ShowTeamPickInfo(ctx, game)

    async def PickTimerHelper(self, ctx, region):
        while True:
            try:
                await asyncio.sleep(Model.TIME_TO_PICK)
                #channel = discord.utils.find(lambda name: name == "General", self.guild.text_channels)
                if not self.games[region]:
                    return
                game = self.games[region]

                playerTurn = self.IdToName(game.playerTurn.id)
                pickedPlayer = game.PickAfk()

                await ctx.send(f'`{playerTurn} ({game.PlayerRace(pickedPlayer.id)}) timed out and chose {self.IdToName(pickedPlayer.id)}`')
                await self.PickShow(ctx, game)
                if game.state == State.IN_GAME:
                    return
            except asyncio.CancelledError:
                return

    async def StartPickTimer(self, ctx, game):
        if game.state != State.IN_GAME:
            await self.CancelPickTimer(game)
            self.autoPickTasks[game.region] = asyncio.create_task(self.PickTimerHelper(ctx, game.region))

    async def CancelPickTimer(self, game):
        if game.region in self.autoPickTasks:
            self.autoPickTasks[game.region].cancel()
            try:
                await self.autoPickTasks[game.region]
            except asyncio.CancelledError:
                pass
            self.autoPickTasks.pop(game.region)

    async def ReportMatchResult(self, ctx, res, playerId):           
        region = self.RegFromPlayer(playerId)
        if region == None:
            await ctx.send(CodeSB(f'Must be a captain in order to report match result'))
            return

        game = self.games[region]
        if game == None or game.state != State.IN_GAME:
            await ctx.send(CodeSB(f'Cannot report result of non-running game'))
            return
        
        oldZElo = [(self.IdToName(player.id), int(player.zelo)) for player in game.zerg.players]
        oldTElo = [(self.IdToName(player.id), int(player.telo)) for player in game.terran.players]
        game.MatchResult(playerId, res)
        for player in itertools.chain(game.zerg.players, game.terran.players):
            self.playerDB.UpdateStats(player)

        newZElo = [(self.IdToName(player.id), int(player.zelo)) for player in game.zerg.players]
        newTElo = [(self.IdToName(player.id), int(player.telo)) for player in game.terran.players]

        embed = discord.Embed(description=f"Victor: {game.GetVictor(playerId, res)}", colour = discord.Colour.blue())

        nameMax = max(len(name) for name, _ in oldZElo)
        strZUpdElos = '\n'.join([f'{oldElo[0].ljust(nameMax)}: {oldElo[1]} -> {newElo[1]}' for oldElo, newElo in zip(oldZElo, newZElo)])
        strTUpdElos = '\n'.join([f'{oldElo[0].ljust(nameMax)}: {oldElo[1]} -> {newElo[1]}' for oldElo, newElo in zip(oldTElo, newTElo)])
        
        embed.add_field(name="Updated Z elo's: ", value=strZUpdElos)
        embed.add_field(name="Updated T elo's: ", value=strTUpdElos)
        await ctx.channel.send(content=CodeSB(f"Match Concluded on {game.region}"), embed=embed)

        await self.EndMatch(ctx, game)

    async def EndMatch(self, ctx, game):
        if game == None:
            return

        self.subs[game.region].clear() 

        await self.DeleteVoice(game)
        self.games[game.region] = None

        if self.queues.is_full(game.region):  
            await self.StartTeamPick(ctx, game.region) 
            await self.ShowQueueStatus(ctx)

    async def ShowQueueStatus(self, ctx):
        embed = discord.Embed(colour = discord.Colour.blue())
        for region, queue in self.queues:
            queued = self.IdsToNames(queue.keys())
            embed.add_field(name=f"{region} [{len(queue)}/{Game.N_PLAYERS}]", value=f"In Queue: {queued}", inline=False)
            if self.games[region] != None and self.games[region].state == State.IN_GAME:
                game = self.games[region]
                zerg = self.IdsToNames(game.zerg.Ids)
                terran = self.IdsToNames(game.terran.Ids)
                runningDuration = int(game.RunningDuration().total_seconds() / 60)
                embed.add_field(name=f"Running for {runningDuration} min", value=f"Zerg: {zerg}\nTerran: {terran}", inline=False)
        await ctx.channel.send(content=None, embed=embed)

    async def PickPlayer(self, ctx, game, choosingPlayer, pickedId, pickedPlayer):
        self.subs[game.region].discard(pickedId)
        game.PickPlayer(pickedId)
        await ctx.send(f'{choosingPlayer} ({game.PlayerRace(pickedId)}) chose {pickedPlayer}')
        await self.PickShow(ctx, game)
        await self.StartPickTimer(ctx, game)

    async def CreateStubs(self, ctx, region, nStubs):
        for id in (i for i in range(1, nStubs + 1)):
            for reg in region.ToList():
                if not self.playerDB.IsRegistered(id, reg):
                    self.playerDB.Register(Player(id, reg))

            await self.AddPlayerQueue(ctx, str(id), id, region, False)

    async def CreateVoice(self, game):
        zergCaptName = self.IdToName(game.zergCapt.id)
        terranCaptName = self.IdToName(game.terranCapt.id)
        zChannelN = f"[{game.region}] {zergCaptName}"
        tChannelN = f"[{game.region}] {terranCaptName}"

        newChannels = set()
        zChannel = await self.guild.create_voice_channel(zChannelN, category = self.category, user_limit=Game.SIZE_ZERG)
        await self.SetVoicePerm(game.zerg.Ids, zChannel)
        newChannels.add(zChannel.id)

        tChannel = await self.guild.create_voice_channel(tChannelN, category = self.category, user_limit=Game.SIZE_TERRAN)
        await self.SetVoicePerm(game.terran.Ids, tChannel)
        newChannels.add(tChannel.id)

        self.privVChannelIds[game.region] = newChannels
        
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
        if not game.region in self.privVChannelIds: #handle canceled match case where voice was never created
            return

        for channelId in self.privVChannelIds[game.region]:
            channel = self.bot.get_channel(channelId)
            if channel:
                await channel.delete()

    def QueueStatus(self):
        return " ".join(f'[{reg}] {len(self.queues[reg])}/{Game.N_PLAYERS}' for reg in Region.REGIONS)
        

    async def ValidateReg(self, ctx, region):
        if not Region.Valid(region):
            await ctx.send(CodeSB(f'Invalid region, expected: {"/".join(Region.VALID_REGIONS)}'))
            return False
        return True

    async def ShowAddQueueStatus(self, ctx, playerName, regionsAddedTo):
        embed = discord.Embed(description = self.QueueStatus(), colour = discord.Colour.blue())
        await ctx.channel.send(content=CodeSB(f'{playerName} added to: {", ".join(regionsAddedTo)}'), embed=embed)

    async def AddPlayerQueue(self, ctx, playerName, playerId, region : Region, showStatus=True):
        regions = region.ToList()

        regionsAddedTo = []
        for reg in regions:
            if playerId not in self.queues[reg]:
                if not any((self.games[newReg] != None and self.games[newReg].IsPlaying(playerId) \
                for newReg in Region.REGIONS)): 
                    self.queues.add(reg, playerId)
                    regionsAddedTo.append(reg)

                    if self.queues.is_full(reg):
                        if self.games[reg]:
                        #      await ctx.send(CodeSB(f'Game on {reg} already running... waiting until it ends'))
                              return

                        for remReg in [r for r in regions if r != reg]:
                            if playerId in self.queues[remReg]:
                                self.queues.remove(remReg, playerId)
                        if showStatus:
                            await self.ShowAddQueueStatus(ctx, playerName, [reg])
                        await self.StartTeamPick(ctx, reg) 
                        return           
        
        if len(regionsAddedTo) == 0:
            await ctx.send(CodeSB(f'{playerName} already added to {", ".join(regions)}'))
            return
        
        if showStatus:
            await self.ShowAddQueueStatus(ctx, playerName, regionsAddedTo)
    
    async def RemPlayerQueue(self, ctx, playerName, playerId, region : Region):
        if self.queues.remove_all_of(region.region, playerId):
            embed = discord.Embed(colour = discord.Colour.blue(), description = self.QueueStatus())
            await ctx.channel.send(content=CodeSB(f'{playerName} removed from: {", ".join(region.ToList())}'), embed=embed)
        else:
            await ctx.send(CodeSB(f'{playerName} not queued on any region'))

    async def AddPlayerSub(self, ctx, playerName, playerId, region : Region):
        regions = region.ToList()

        if any((self.games[reg] and (playerId in self.games[reg].AllPlayers) for reg in regions)):
            await ctx.send(CodeSB(f'Cannot sub when in game or in player pool'))
            return

        subbedRegs = []
        for reg in regions:
            if self.games[reg]:
                self.subs[reg].add(playerId)
                subbedRegs.append(reg)

        if len(subbedRegs) == 0:
            await ctx.send(CodeSB(f'No game found to sub/already in a pool'))
        else:
            await ctx.send(CodeSB(f'{playerName} now avaiable to sub on {", ".join(subbedRegs)}'))

    async def RemPlayerSub(self, ctx, playerName, playerId, region : Region):
        regions = region.ToList()

        for reg in regions:
            self.subs[reg].discard(playerId)
        
        await ctx.send(CodeSB(f'{playerName} no longer avaiable to sub on {", ".join(regions)}'))

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