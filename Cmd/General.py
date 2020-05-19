import discord
from discord.ext import commands
from Model import Model
import itertools
from datetime import datetime

from Game import Game, State
from Player import Player, MatchRes, Race
from Region import Region
from Utility import CodeB, CodeSB

class General(commands.Cog,):  
    CMD_RATE = 2
    CMD_COOLDOWN = 10   
    def __init__(self, model):
        self.model = model

    @commands.command(name='reg', help='Register with the server to play private games (registration is required to run all other commands)')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_register(self, ctx):
        playerId = ctx.message.author.id
        playerName = ctx.message.author.name

        registeredRegs = []
        for reg in Region.REGIONS:
            res = self.model.playerDB.IsRegistered(playerId, reg)
            if not res:
                self.model.playerDB.Register(Player(playerId, reg))
                registeredRegs.append(reg)

        if len(registeredRegs) == 0:
            await ctx.send(f'{playerName} already registered')
            return
        else:
            await ctx.send(f'{playerName} successfully registered on {", ".join(registeredRegs)}')

    
    async def ShowAddQueueStatus(self, ctx, playerName, regionsAddedTo):
        embed = discord.Embed(colour = discord.Colour.blue(), description = self.model.QueueStatus())
        await ctx.channel.send(content=CodeSB(f'{playerName} added to: {", ".join(regionsAddedTo)}'), embed=embed)

    @commands.command(name='addsub', help='Allow yourself to be a potential sub on region (captains must already be picking)')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_sub(self, ctx, region : Region = Region(Region.ALL)):
        if not self.model.ChkIsReg(ctx):
            return

        playerName = ctx.message.author.name
        playerId = ctx.message.author.id

        regions = region.ToList()

        if any((self.model.games[reg] and ((self.model.games[reg].state == State.IN_GAME) \
        or (playerId in self.model.games[reg].PoolIds)) for reg in regions)):
            await ctx.send(CodeSB(f'Cannot sub when in game or in player pool'))
            return

        subbedRegs = []
        for reg in regions:
            if self.model.games[reg]:
                self.model.subs[reg].add(playerId)
                subbedRegs.append(reg)

        if len(subbedRegs) == 0:
            await ctx.send(CodeSB(f'No game found to sub/already in a pool'))
        else:
            await ctx.send(CodeSB(f'{playerName} now avaiable to sub on {", ".join(subbedRegs)}'))

    @commands.command(name='delsub', aliases = ['remsub'], help='Remove yourself as potential sub on region')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_del_sub(self, ctx, region : Region = Region(Region.ALL)):
        if not self.model.ChkIsReg(ctx):
            return

        playerName = ctx.message.author.name
        playerId = ctx.message.author.id

        regions = region.ToList()

        for reg in regions:
            self.model.subs[reg].discard(playerId)
        
        await ctx.send(CodeSB(f'{playerName} no longer avaiable to sub on {", ".join(regions)}'))

    @commands.command(name='add', help=f'Add to queue on region (NA/EU/ALL = default); Timeout={Model.QUEUE_TIMEOUT} mins', ignore_extra=False)
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_add(self, ctx, region : Region = Region(Region.ALL)):
        if not self.model.ChkIsReg(ctx):
            return

        player = ctx.message.author.name
        playerId = ctx.message.author.id

        regions = region.ToList()

        regionsAddedTo = []
        for reg in regions:
            if playerId not in self.model.queues[reg]:
                if not any((self.model.games[newReg] != None and self.model.games[newReg].IsPlaying(playerId) \
                for newReg in Region.REGIONS)): 
                    if len(self.model.queues[reg]) == Game.N_PLAYERS and \
                    self.model.games[reg].state == State.IN_GAME:
                        await ctx.send(f"{reg}'s queue is full")
                        return
                    self.model.queues.add(reg, playerId)
                    regionsAddedTo.append(reg)

                    if len(self.model.queues[reg]) == Game.N_PLAYERS:
                        for remReg in [r for r in regions if r != reg]:
                            if playerId in self.model.queues[remReg]:
                                self.model.queues.remove(remReg, playerId)
                        await self.ShowAddQueueStatus(ctx, player, [reg])
                        await self.model.StartTeamPick(ctx, reg) 
                        return           
        
        if len(regionsAddedTo) == 0:
            await ctx.send(f'{player} already added to {", ".join(regions)}')
            return
        
        await self.ShowAddQueueStatus(ctx, player, regionsAddedTo)
                
    @commands.command(name='del', aliases = ['rem'], help='Remove yourself from queue on region (NA/EU/ALL = default)', ignore_extra=False)
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_remove(self, ctx, region : Region = Region(Region.ALL)):
        if not self.model.ChkIsReg(ctx):
            return

        playerId = ctx.message.author.id
        playerName = ctx.message.author.name

        if self.model.queues.remove_all_of(region.region, playerId):
            embed = discord.Embed(colour = discord.Colour.blue(), description = self.model.QueueStatus())
            await ctx.channel.send(content=CodeSB(f'{playerName} removed from: {", ".join(region.ToList())}'), embed=embed)
        else:
            await ctx.send(CodeSB(f'{playerName} not queued on any region'))
        
    @commands.command(name='stats', help='Retreive stats of player', ignore_extra=False)
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_stats(self, ctx, member : discord.Member):
        if not (self.model.ChkIsReg(ctx) and self.model.ChkIsRegId(member.id)):
            return

        playerName = member.name

        embed = discord.Embed(colour = discord.Colour.blue())
        for region in Region.REGIONS:
            usPlayer = self.model.playerDB.Find(member.id, region)
            if usPlayer and usPlayer.lastPlayed:
                stats = []
                for race in Race.RACES:
                    wins, loses, ties, elo = usPlayer.wins[race], usPlayer.loses[race], usPlayer.ties[race], usPlayer.elo[race]
                    elo = f'{int(elo)}'.ljust(4)
                    winPer = (f'{usPlayer.Ratio(race)*100:.1f}' if (wins + loses > 0) else '-').ljust(5)

                    stats.append(f'''[{race}] Win %\tElo\tWin/Loss/Tie
\t{winPer}\t{elo}   {wins}/{loses}/{ties}''')

            msg = "\n\n".join(stats)
            msg += f'\n\nLast Played: {usPlayer.lastPlayed}'

            embed.add_field(name=region, value=CodeB(msg, "ml"), inline = False)

        await ctx.channel.send(content=f"`Stats {playerName}`", embed=embed)

    @commands.command(name='status', help='Query status of queue and any running games')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_status(self, ctx):
        if not self.model.ChkIsReg(ctx):
            return

        embed = discord.Embed(colour = discord.Colour.blue())
        for region, queue in self.model.queues:
            queued = self.model.IdsToNames(queue.keys())
            embed.add_field(name=f"{region} [{len(queue)}/{Game.N_PLAYERS}]", value=f"In Queue: {queued}", inline=False)
            if self.model.games[region] != None and self.model.games[region].state == State.IN_GAME:
                game = self.model.games[region]
                zerg = self.model.IdsToNames(game.zerg.Ids)
                terran = self.model.IdsToNames(game.terran.Ids)
                runningDuration = int(game.RunningDuration().total_seconds() / 60)
                embed.add_field(name=f"Running for {runningDuration} min", value=f"Zerg: {zerg}\nTerran: {terran}", inline=False)
        await ctx.channel.send(content=None, embed=embed)

    @commands.command(name='racepref', help='Set/query race preference for region (Z - Zerg, T - Terran, A - Any)')
    @commands.cooldown(CMD_RATE, CMD_COOLDOWN)
    async def on_set_racepref(self, ctx, racePref : Race, region : Region = Region(Region.ALL)):
        if not self.model.ChkIsReg(ctx):
            return

        playerId = ctx.message.author.id
        playerName = ctx.message.author.name

        #if not(racePref >= Race.ZERG and racePref <= Race.ANY):
        #    await ctx.send(f'Invalid race preference; expected (0 = ZERG, 1 = TERRAN, 2 = ANY)')
        #    return
#
        #racePref = RacePref(racePref)
        regions = region.ToList()
        for reg in regions:
            usPlayer = self.model.playerDB.Find(playerId, reg)
            if usPlayer == None:
                await ctx.send(f'Player {playerName} not registered')

            usPlayer.racePref = racePref
            self.model.playerDB.UpdateStats(usPlayer)

        await ctx.send(CodeSB(f"{playerName}'s preference updated to {racePref.race} on {', '.join(regions)}"))