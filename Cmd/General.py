from discord.ext import commands
from Model import Model
import itertools
import discord
from datetime import datetime

from Game import Game, State
from Player import Player, MatchRes
import Region
from Utility import CodeB

class General(commands.Cog):     
    def __init__(self, model):
        self.model = model

    @commands.command(name='reg', help='Register with the server to play private games (registration is required to run all other commands)')
    @commands.cooldown(2, 10)
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
            await ctx.send(f'{playerName} successfully registered on {registeredRegs}')

    @commands.command(name='add', help='Add to queue on region (NA/EU/ALL = default)')
    @commands.cooldown(2, 10)
    async def on_add(self, ctx, region : str ='ALL'):
        if not self.model.ChkIsReg(ctx):
            return

        if not await self.model.ValidateReg(ctx, region):
            return

        player = ctx.message.author.name
        playerId = ctx.message.author.id

        regions = Region.ToList(region)

        regionAddedTo = []
        for reg in regions:
            if True: #playerId not in queues[region].Ids:
                if not any((self.model.games[newReg] != None and self.model.games[newReg].IsPlaying(playerId) \
                for newReg in Region.REGIONS)): 
                    if len(self.model.queues[reg]) == Game.N_PLAYERS and \
                    self.model.games[reg].state == State.IN_GAME:
                        await ctx.send(f"{reg}'s queue is full")
                        return
                    self.model.queues.add(reg, playerId)
                    regionAddedTo.append(reg)

                    if len(self.model.queues[reg]) == Game.N_PLAYERS:
                        await self.model.StartTeamPick(ctx, reg)            
        
        if len(regionAddedTo) == 0:
            await ctx.send(f'{player} already added to {" ".join(regions)}')
            return
        
        embed = discord.Embed(colour = discord.Colour.blue(), description = self.QueueStatus())
        await ctx.channel.send(content=f'{player} added to: {", ".join(regionAddedTo)}', embed=embed)

    def QueueStatus(self):
        return " ".join(f'[{reg}] {len(self.model.queues[reg])}/{Game.N_PLAYERS}' for reg in Region.REGIONS)
                
    @commands.command(name='rem', help='Remove from current queue on region (NA/EU/ALL = default)')
    @commands.cooldown(2, 10)
    async def on_remove(self, ctx, region : str = 'ALL'):
        if not self.model.ChkIsReg(ctx):
            return
        
        if not await self.model.ValidateReg(ctx, region):
            return

        regions = Region.ToList(region)

        playerId = ctx.message.author.id
        playerName = ctx.message.author.name

        self.model.queues.remove_all_of(region, playerId)

        embed = discord.Embed(colour = discord.Colour.blue(), description = self.QueueStatus())
        await ctx.channel.send(content=f'{playerName} removed from: {", ".join(regions)}', embed=embed)
        
    @commands.command(name='stats', help='Retreive stats of player', ignore_extra=False)
    @commands.cooldown(2, 10)
    async def on_stats(self, ctx, member : discord.Member):
        if not self.model.ChkIsReg(ctx):
            return

        playerName = member.name

        embed = discord.Embed(colour = discord.Colour.blue())
        for region in Region.REGIONS:
            usPlayer = self.model.playerDB.Find(member.id, region)
            if usPlayer and usPlayer.lastPlayed:
                ties = usPlayer.games - usPlayer.wins - usPlayer.loses
                elo = f'{int(usPlayer.elo)}'.ljust(4)
                winPer = f'{usPlayer.Ratio*100:.1f}'.ljust(5)

                msg = f'''Win %\tElo\tLast Played
{winPer}\t{elo}   {usPlayer.lastPlayed}

Win/Loss/Tie
{usPlayer.wins}/{usPlayer.loses}/{ties}
'''

                embed.add_field(name=region, value=CodeB(msg, "ml"), inline = False)
        await ctx.channel.send(content=f"`Stats {playerName}`", embed=embed)

    @commands.command(name='status', help='Query status of queue and any running games')
    @commands.cooldown(2, 10)
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